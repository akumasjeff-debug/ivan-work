/**
 * 電玩庫存表 — Google Sheet 建置＋寫入端點 v4
 *
 * 分頁一「庫存表」＝最新快照，七欄（對接 PChome 廠商商品匯出檔）：
 *   廠商名稱 | 商品編號 | 商品名稱 | 可賣量 | 成本 | 售價 | 來源廠商
 * 分頁二「可賣量歷史」＝一列一商品、一欄一匯入日期，
 *   每次匯入自動加當天日期欄，各週可賣量並排看差距（每週一比對用）。
 *
 * 一次性設定：
 *   1. 試算表 → 擴充功能 → Apps Script，貼上本檔全部內容，執行 setup（跳授權照按）
 *   2. 左側「專案設定」→ 指令碼屬性 → 新增屬性：API_TOKEN = （本機 config.local.json 裡的 token）
 *   3. 右上「部署」→ 新增部署作業 → 類型「網頁應用程式」→ 執行身分「我」、
 *      存取權「任何人」→ 部署 → 複製網頁應用程式網址，填回本機 config.local.json 的 webapp_url
 *
 * 注意：之後若改了本檔程式碼，要「部署 → 管理部署作業 → 編輯 → 新版本」才會生效。
 * 重跑 setup 不會清資料，只重設標題列、格式與條件格式。
 */

var SHEET_STOCK = '庫存表';
var SHEET_HISTORY = '可賣量歷史';
var STOCK_COLS = 7;
var MAX_ROWS = 2000; // 格式套用列數上限，商品超過再調大重跑

function setup() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  ss.setSpreadsheetLocale('zh_TW');
  buildStock_(ss);
  historySheet_(ss); // 沒有就先建好
  ss.setActiveSheet(ss.getSheetByName(SHEET_STOCK));
}

function headerStyle_(range) {
  return range.setFontWeight('bold').setBackground('#263238').setFontColor('#ffffff');
}

function buildStock_(ss) {
  var sh = ss.getSheetByName(SHEET_STOCK) || ss.insertSheet(SHEET_STOCK, 0);
  var headers = ['廠商名稱', '商品編號', '商品名稱', '可賣量', '成本', '售價', '來源廠商'];
  headerStyle_(sh.getRange(1, 1, 1, headers.length).setValues([headers]));
  sh.setFrozenRows(1);

  sh.getRange('B2:B' + MAX_ROWS).setNumberFormat('@'); // 商品編號 20 碼保文字
  sh.getRange('D2:F' + MAX_ROWS).setNumberFormat('#,##0');
  sh.getRange('G2:G' + MAX_ROWS).setNumberFormat('0'); // 來源廠商編號不加千分位
  sh.setColumnWidth(2, 190);  // 商品編號
  sh.setColumnWidth(3, 380);  // 商品名稱

  // 可賣量 = 0 整列標紅（缺貨一眼看出）
  var outOfStock = SpreadsheetApp.newConditionalFormatRule()
    .setRanges([sh.getRange('A2:G' + MAX_ROWS)])
    .whenFormulaSatisfied('=AND($B2<>"",$D2=0)')
    .setBackground('#fce4ec').setFontColor('#c62828')
    .build();
  sh.setConditionalFormatRules([outOfStock]);

  // 標題列篩選器（可依廠商/可賣量排序過濾）
  if (sh.getFilter()) sh.getFilter().remove();
  sh.getRange('A1:G' + MAX_ROWS).createFilter();
}

function historySheet_(ss) {
  var sh = ss.getSheetByName(SHEET_HISTORY);
  if (!sh) {
    sh = ss.insertSheet(SHEET_HISTORY);
    headerStyle_(sh.getRange(1, 1, 1, 2).setValues([['商品編號', '商品名稱']]));
    sh.setFrozenRows(1);
    sh.setFrozenColumns(2);
    sh.getRange('A2:A' + MAX_ROWS).setNumberFormat('@');
    sh.setColumnWidth(1, 190);
    sh.setColumnWidth(2, 380);
  }
  return sh;
}

/**
 * 歷史分頁：以商品編號對列，寫入 dateLabel 欄（同日期重跑＝覆蓋同一欄，
 * 否則在最右加新欄）；新商品自動補列，這次匯出沒有的商品該欄留白。
 */
function updateHistory_(ss, rows, dateLabel) {
  var sh = historySheet_(ss);
  var lastRow = sh.getLastRow();
  var lastCol = sh.getLastColumn();

  var header = sh.getRange(1, 1, 1, lastCol).getValues()[0];
  var col = header.indexOf(dateLabel) + 1;
  if (col === 0) {
    col = lastCol + 1;
    headerStyle_(sh.getRange(1, col).setValue(dateLabel));
    sh.setColumnWidth(col, 95);
    sh.getRange(2, col, MAX_ROWS - 1, 1).setNumberFormat('#,##0');
  }

  var idMap = {};
  if (lastRow > 1) {
    var ids = sh.getRange(2, 1, lastRow - 1, 1).getValues();
    for (var i = 0; i < ids.length; i++) idMap[String(ids[i][0])] = i + 2;
  }

  // 先補新商品的列（批次一次寫）
  var newRows = [];
  rows.forEach(function (r) {
    var id = String(r[1]);
    if (!idMap[id]) {
      idMap[id] = lastRow + 1 + newRows.length;
      newRows.push([id, r[2]]);
    }
  });
  if (newRows.length) sh.getRange(lastRow + 1, 1, newRows.length, 2).setValues(newRows);

  // 整欄一次寫入這次的可賣量；沒出現在這次匯出的商品留白
  var dataRows = lastRow - 1 + newRows.length;
  var colVals = [];
  for (var k = 0; k < dataRows; k++) colVals.push(['']);
  rows.forEach(function (r) { colVals[idMap[String(r[1])] - 2] = [r[3]]; });
  sh.getRange(2, col, dataRows, 1).setValues(colVals);
}

/**
 * Web App 寫入端點：本機 匯入轉換.py POST JSON {token, date, rows:[[七欄]...]}，
 * 驗 token（存指令碼屬性 API_TOKEN，不進 git）後：
 *   1. 整份覆蓋「庫存表」資料列（最新快照）
 *   2. 「可賣量歷史」寫入 date 那欄
 */
function doPost(e) {
  var out = { ok: false };
  try {
    var body = JSON.parse(e.postData.contents);
    var token = PropertiesService.getScriptProperties().getProperty('API_TOKEN');
    if (!token || body.token !== token) {
      out.error = 'bad token';
      return json_(out);
    }
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sh = ss.getSheetByName(SHEET_STOCK);
    if (!sh) { buildStock_(ss); sh = ss.getSheetByName(SHEET_STOCK); }
    var rows = body.rows || [];
    var last = sh.getLastRow();
    if (last > 1) sh.getRange(2, 1, last - 1, sh.getLastColumn()).clearContent();
    if (rows.length) sh.getRange(2, 1, rows.length, rows[0].length).setValues(rows);

    var dateLabel = body.date ||
      Utilities.formatDate(new Date(), 'Asia/Taipei', 'yyyy-MM-dd');
    if (rows.length) updateHistory_(ss, rows, dateLabel);

    out.ok = true;
    out.written = rows.length;
    out.dateColumn = dateLabel;
    out.updatedAt = Utilities.formatDate(new Date(), 'Asia/Taipei', 'yyyy-MM-dd HH:mm:ss');
  } catch (err) {
    out.error = String(err);
  }
  return json_(out);
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
