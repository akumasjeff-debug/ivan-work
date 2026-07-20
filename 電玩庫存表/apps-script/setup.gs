/**
 * 電玩庫存表 — Google Sheet 一鍵建置腳本
 *
 * 使用方式：
 *   1. 開一個全新的 Google 試算表（sheets.new）
 *   2. 擴充功能 → Apps Script，把本檔全部內容貼進去（取代預設程式碼）
 *   3. 上方選單選 setup → 執行（第一次會跳授權，照按同意）
 *   4. 回到試算表，四個分頁都建好即可開始使用；之後 Apps Script 可留可刪
 *
 * 重跑 setup 不會清掉已輸入的資料列，只會重設標題列、格式、下拉驗證與公式。
 */

var SHEET_MASTER = '商品主檔';
var SHEET_IN = '進貨紀錄';
var SHEET_OUT = '出貨紀錄';
var SHEET_SUMMARY = '庫存總覽';

var PLATFORMS = ['PS5', 'PS4', 'NS', 'NS2', 'Xbox', '周邊', '其他'];
var TYPES = ['遊戲', '主機', '周邊', '其他'];
var CHANNELS = ['PChome', 'momo', '蝦皮', '店面', '其他'];
var MAX_ROWS = 1000; // 下拉驗證與格式套用的列數上限，不夠再拉高重跑

function setup() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  ss.setSpreadsheetLocale('zh_TW');

  buildMaster_(ss);   // 先建主檔，進出貨的品名下拉要引用它
  buildInbound_(ss);
  buildOutbound_(ss);
  buildSummary_(ss);

  // 刪掉新試算表預設的空白分頁
  var def = ss.getSheetByName('工作表1') || ss.getSheetByName('Sheet1');
  if (def && ss.getSheets().length > 4) ss.deleteSheet(def);

  ss.setActiveSheet(ss.getSheetByName(SHEET_SUMMARY));
}

function getOrCreate_(ss, name) {
  return ss.getSheetByName(name) || ss.insertSheet(name);
}

function setHeader_(sh, headers) {
  sh.getRange(1, 1, 1, headers.length).setValues([headers])
    .setFontWeight('bold').setBackground('#263238').setFontColor('#ffffff');
  sh.setFrozenRows(1);
}

function listRule_(values) {
  return SpreadsheetApp.newDataValidation()
    .requireValueInList(values, true).setAllowInvalid(true).build();
}

function masterNameRule_(ss) {
  var master = ss.getSheetByName(SHEET_MASTER);
  return SpreadsheetApp.newDataValidation()
    .requireValueInRange(master.getRange('A2:A' + MAX_ROWS), true)
    .setAllowInvalid(true).build();
}

/** 商品主檔：品名（唯一鍵）| 平台 | 類型 | 條碼 | 預設成本 | 售價 | 備註 */
function buildMaster_(ss) {
  var sh = getOrCreate_(ss, SHEET_MASTER);
  setHeader_(sh, ['品名', '平台', '類型', '條碼', '預設成本', '售價', '備註']);
  sh.getRange('B2:B' + MAX_ROWS).setDataValidation(listRule_(PLATFORMS));
  sh.getRange('C2:C' + MAX_ROWS).setDataValidation(listRule_(TYPES));
  sh.getRange('D2:D' + MAX_ROWS).setNumberFormat('@'); // 條碼保留前導零
  sh.getRange('E2:F' + MAX_ROWS).setNumberFormat('#,##0');
  sh.setColumnWidth(1, 280);
}

/** 進貨紀錄：日期 | 品名 | 數量 | 進貨單價 | 小計（自動）| 廠商 | 備註 */
function buildInbound_(ss) {
  var sh = getOrCreate_(ss, SHEET_IN);
  setHeader_(sh, ['日期', '品名', '數量', '進貨單價', '小計', '廠商', '備註']);
  sh.getRange('A2:A' + MAX_ROWS).setNumberFormat('yyyy-mm-dd');
  sh.getRange('B2:B' + MAX_ROWS).setDataValidation(masterNameRule_(ss));
  sh.getRange('C2:C' + MAX_ROWS).setNumberFormat('#,##0');
  sh.getRange('D2:E' + MAX_ROWS).setNumberFormat('#,##0');
  sh.getRange('E2').setFormula('=ARRAYFORMULA(IF(B2:B="",,C2:C*D2:D))');
  sh.setColumnWidth(2, 280);
}

/** 出貨紀錄：日期 | 品名 | 數量 | 通路 | 出貨單價 | 小計（自動）| 備註 */
function buildOutbound_(ss) {
  var sh = getOrCreate_(ss, SHEET_OUT);
  setHeader_(sh, ['日期', '品名', '數量', '通路', '出貨單價', '小計', '備註']);
  sh.getRange('A2:A' + MAX_ROWS).setNumberFormat('yyyy-mm-dd');
  sh.getRange('B2:B' + MAX_ROWS).setDataValidation(masterNameRule_(ss));
  sh.getRange('C2:C' + MAX_ROWS).setNumberFormat('#,##0');
  sh.getRange('D2:D' + MAX_ROWS).setDataValidation(listRule_(CHANNELS));
  sh.getRange('E2:F' + MAX_ROWS).setNumberFormat('#,##0');
  sh.getRange('F2').setFormula('=ARRAYFORMULA(IF(B2:B="",,C2:C*E2:E))');
  sh.setColumnWidth(2, 280);
}

/**
 * 庫存總覽（除「安全庫存、備註」外全自動，勿手動輸入）：
 * 品名 | 平台 | 總進貨 | 總出貨 | 現有庫存 | 平均進價 | 安全庫存（手填）| 備註
 * 現有庫存 <= 安全庫存 時整列標紅。
 */
function buildSummary_(ss) {
  var sh = getOrCreate_(ss, SHEET_SUMMARY);
  setHeader_(sh, ['品名', '平台', '總進貨', '總出貨', '現有庫存', '平均進價', '安全庫存', '備註']);
  sh.getRange('A2').setFormula(
    "=IFERROR(FILTER('" + SHEET_MASTER + "'!A2:B,'" + SHEET_MASTER + "'!A2:A<>\"\"),)");
  sh.getRange('C2').setFormula(
    "=ARRAYFORMULA(IF(A2:A=\"\",,SUMIF('" + SHEET_IN + "'!B:B,A2:A,'" + SHEET_IN + "'!C:C)))");
  sh.getRange('D2').setFormula(
    "=ARRAYFORMULA(IF(A2:A=\"\",,SUMIF('" + SHEET_OUT + "'!B:B,A2:A,'" + SHEET_OUT + "'!C:C)))");
  sh.getRange('E2').setFormula('=ARRAYFORMULA(IF(A2:A="",,C2:C-D2:D))');
  sh.getRange('F2').setFormula(
    "=ARRAYFORMULA(IF((A2:A=\"\")+(C2:C=0),,ROUND(SUMIF('" + SHEET_IN + "'!B:B,A2:A,'" + SHEET_IN + "'!E:E)/C2:C,0)))");
  sh.getRange('C2:G' + MAX_ROWS).setNumberFormat('#,##0');
  sh.setColumnWidth(1, 280);

  var lowStock = SpreadsheetApp.newConditionalFormatRule()
    .setRanges([sh.getRange('A2:H' + MAX_ROWS)])
    .whenFormulaSatisfied('=AND($A2<>"",$G2<>"",$E2<=$G2)')
    .setBackground('#fce4ec').setFontColor('#c62828')
    .build();
  sh.setConditionalFormatRules([lowStock]);
}
