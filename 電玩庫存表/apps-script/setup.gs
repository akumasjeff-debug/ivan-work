/**
 * 電玩庫存表 — Google Sheet 建置＋寫入端點 v5
 *
 * 分頁（全部由本機 匯入轉換.py 經 doPost 寫入，缺的分頁會自動建）：
 *   庫存表（pchome採購快照）、含庫存廠商頁（傑仕登/宏碁遊戲）→ stock 版面 12 欄
 *   純銷量廠商頁（壹世代…等 8 頁）→ sales 版面 7 欄
 *   可賣量歷史（一欄一日期）、週銷歷史（一欄一週）→ 一列一商品
 *
 * stock 版面：首欄 | 商品編號 | 商品名稱 | 可賣量 | 成本 | 售價 | 來源廠商
 *             | 週銷 MM/DD-MM/DD | 可售週數 | 業績金額 | 毛利額 | 毛利率
 *   警示：可賣量0且週銷>0＝深紅（最優先補貨）；可賣量0＝淺紅；可售週數<1＝橘。
 * sales 版面：商品編號 | 商品名稱 | 館名稱 | 週銷 | 業績金額 | 毛利額 | 毛利率
 *
 * 一次性設定（已完成過就只要重貼程式碼＋重新部署新版本）：
 *   1. 貼上本檔全部內容，執行 setup（跳授權照按）
 *   2. 專案設定 → 指令碼屬性：API_TOKEN =（本機 config.local.json 的 token）
 *   3. 部署 → 新增部署作業 → 網頁應用程式（執行身分「我」、存取權「任何人」）
 * 注意：改程式碼後要「部署 → 管理部署作業 → 編輯 → 新版本」才會生效。
 */

var SHEET_STOCK = '庫存表';
var SHEET_QTY_HIST = '可賣量歷史';
var SHEET_SALES_HIST = '週銷歷史';
var TAB_MAX_ROWS = 3000;    // 各廠商分頁格式套用上限
var HIST_MAX_ROWS = 12000;  // 歷史分頁格式套用上限

function setup() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  ss.setSpreadsheetLocale('zh_TW');
  var sh = ss.getSheetByName(SHEET_STOCK) || ss.insertSheet(SHEET_STOCK, 0);
  headerStyle_(sh.getRange(1, 1, 1, 12).setValues([[
    '廠商名稱', '商品編號', '商品名稱', '可賣量', '成本', '售價',
    '來源廠商', '週銷', '可售週數', '業績金額', '毛利額', '毛利率']]));
  formatStock_(sh);
  histSheet_(ss, SHEET_QTY_HIST);
  histSheet_(ss, SHEET_SALES_HIST);
  ss.setActiveSheet(sh);
}

function headerStyle_(range) {
  return range.setFontWeight('bold').setBackground('#263238').setFontColor('#ffffff');
}

function formatStock_(sh) {
  sh.setFrozenRows(1);
  sh.getRange('B2:B' + TAB_MAX_ROWS).setNumberFormat('@');       // 商品編號保文字
  sh.getRange('D2:F' + TAB_MAX_ROWS).setNumberFormat('#,##0');
  sh.getRange('G2:G' + TAB_MAX_ROWS).setNumberFormat('0');       // 來源廠商編號
  sh.getRange('H2:H' + TAB_MAX_ROWS).setNumberFormat('#,##0');   // 週銷
  sh.getRange('I2:I' + TAB_MAX_ROWS).setNumberFormat('0.0');     // 可售週數
  sh.getRange('J2:K' + TAB_MAX_ROWS).setNumberFormat('#,##0');   // 業績/毛利額
  sh.getRange('L2:L' + TAB_MAX_ROWS).setNumberFormat('0.0%');    // 毛利率
  sh.setColumnWidth(2, 190);
  sh.setColumnWidth(3, 380);

  var rules = [
    // 缺貨但本週有銷量 → 深紅（最優先補貨）
    SpreadsheetApp.newConditionalFormatRule()
      .setRanges([sh.getRange('A2:L' + TAB_MAX_ROWS)])
      .whenFormulaSatisfied('=AND($B2<>"",$D2=0,$H2>0)')
      .setBackground('#b71c1c').setFontColor('#ffffff').build(),
    // 缺貨 → 淺紅
    SpreadsheetApp.newConditionalFormatRule()
      .setRanges([sh.getRange('A2:L' + TAB_MAX_ROWS)])
      .whenFormulaSatisfied('=AND($B2<>"",$D2=0)')
      .setBackground('#fce4ec').setFontColor('#c62828').build(),
    // 庫存撐不到一週 → 橘
    SpreadsheetApp.newConditionalFormatRule()
      .setRanges([sh.getRange('A2:L' + TAB_MAX_ROWS)])
      .whenFormulaSatisfied('=AND($B2<>"",$D2>0,$H2>0,$I2<1)')
      .setBackground('#fff3e0').setFontColor('#e65100').build()
  ];
  sh.setConditionalFormatRules(rules);

  if (sh.getFilter()) sh.getFilter().remove();
  sh.getRange('A1:L' + TAB_MAX_ROWS).createFilter();
}

function formatSales_(sh) {
  sh.setFrozenRows(1);
  sh.getRange('A2:A' + TAB_MAX_ROWS).setNumberFormat('@');
  sh.getRange('D2:F' + TAB_MAX_ROWS).setNumberFormat('#,##0');
  sh.getRange('G2:G' + TAB_MAX_ROWS).setNumberFormat('0.0%');
  sh.setColumnWidth(1, 190);
  sh.setColumnWidth(2, 380);
  if (sh.getFilter()) sh.getFilter().remove();
  sh.getRange('A1:G' + TAB_MAX_ROWS).createFilter();
}

function histSheet_(ss, name) {
  var sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    headerStyle_(sh.getRange(1, 1, 1, 2).setValues([['商品編號', '商品名稱']]));
    sh.setFrozenRows(1);
    sh.setFrozenColumns(2);
    sh.getRange('A2:A' + HIST_MAX_ROWS).setNumberFormat('@');
    sh.setColumnWidth(1, 190);
    sh.setColumnWidth(2, 380);
  }
  return sh;
}

/** 分頁整份覆蓋：標題列每次重寫（週銷欄標日期），缺分頁自動建＋套格式。 */
function writeTab_(ss, tab) {
  var sh = ss.getSheetByName(tab.name);
  var isNew = !sh;
  if (isNew) sh = ss.insertSheet(tab.name);
  headerStyle_(sh.getRange(1, 1, 1, tab.headers.length).setValues([tab.headers]));
  if (isNew) (tab.type === 'stock' ? formatStock_ : formatSales_)(sh);
  var last = sh.getLastRow();
  if (last > 1) sh.getRange(2, 1, last - 1, sh.getLastColumn()).clearContent();
  if (tab.rows.length) {
    sh.getRange(2, 1, tab.rows.length, tab.headers.length).setValues(tab.rows);
  }
}

/**
 * 歷史分頁：以商品編號對列，寫入 label 欄（同 label 重跑＝覆蓋同一欄，
 * 否則最右加新欄）；新商品自動補列，這次沒出現的商品該欄留白。
 * entries = [[商品編號, 商品名稱, 數值], ...]
 */
function updateHistory_(ss, name, entries, label) {
  var sh = histSheet_(ss, name);
  var lastRow = sh.getLastRow();
  var lastCol = sh.getLastColumn();

  var header = sh.getRange(1, 1, 1, lastCol).getValues()[0];
  var col = header.indexOf(label) + 1;
  if (col === 0) {
    col = lastCol + 1;
    headerStyle_(sh.getRange(1, col).setValue(label));
    sh.setColumnWidth(col, 105);
    sh.getRange(2, col, HIST_MAX_ROWS - 1, 1).setNumberFormat('#,##0');
  }

  var idMap = {};
  if (lastRow > 1) {
    var ids = sh.getRange(2, 1, lastRow - 1, 1).getValues();
    for (var i = 0; i < ids.length; i++) idMap[String(ids[i][0])] = i + 2;
  }

  var newRows = [];
  entries.forEach(function (e) {
    var id = String(e[0]);
    if (!idMap[id]) {
      idMap[id] = lastRow + 1 + newRows.length;
      newRows.push([id, e[1]]);
    }
  });
  if (newRows.length) sh.getRange(lastRow + 1, 1, newRows.length, 2).setValues(newRows);

  var dataRows = lastRow - 1 + newRows.length;
  var colVals = [];
  for (var k = 0; k < dataRows; k++) colVals.push(['']);
  entries.forEach(function (e) { colVals[idMap[String(e[0])] - 2] = [e[2]]; });
  sh.getRange(2, col, dataRows, 1).setValues(colVals);
}

/**
 * Web App 寫入端點：本機 匯入轉換.py POST JSON
 *   {token, date, weekLabel, tabs:[{name,type,headers,rows}], qtyHistory, salesHistory}
 * 驗 token（指令碼屬性 API_TOKEN）後：各分頁整份覆蓋＋兩個歷史分頁各寫一欄。
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
    (body.tabs || []).forEach(function (t) { writeTab_(ss, t); });
    if (body.qtyHistory && body.qtyHistory.length) {
      updateHistory_(ss, SHEET_QTY_HIST, body.qtyHistory, body.date);
    }
    if (body.salesHistory && body.salesHistory.length) {
      updateHistory_(ss, SHEET_SALES_HIST, body.salesHistory, body.weekLabel);
    }
    out.ok = true;
    out.tabs = (body.tabs || []).map(function (t) { return t.name + ':' + t.rows.length; });
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
