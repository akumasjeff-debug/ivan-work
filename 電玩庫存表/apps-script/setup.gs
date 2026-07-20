/**
 * 電玩庫存表 — Google Sheet 建置＋寫入端點 v3
 *
 * 六欄格式（對接 PChome 廠商商品匯出檔）：
 *   廠商名稱 | 商品編號 | 商品名稱 | 可賣量 | 成本 | 售價
 *
 * 一次性設定：
 *   1. 試算表 → 擴充功能 → Apps Script，貼上本檔全部內容，執行 setup（跳授權照按）
 *   2. 左側「專案設定」→ 指令碼屬性 → 新增屬性：API_TOKEN = （本機 config.local.json 裡的 token）
 *   3. 右上「部署」→ 新增部署作業 → 類型「網頁應用程式」→ 執行身分「我」、
 *      存取權「任何人」→ 部署 → 複製網頁應用程式網址，填回本機 config.local.json 的 webapp_url
 *   之後本機跑 匯入轉換.py 就會直接寫進「庫存表」，不用手動貼。
 *
 * 注意：之後若改了本檔程式碼，要「部署 → 管理部署作業 → 編輯 → 新版本」才會生效。
 * 重跑 setup 不會清資料，只重設標題列、格式與條件格式。
 */

var SHEET_STOCK = '庫存表';
var MAX_ROWS = 2000; // 格式套用列數上限，商品超過再調大重跑

function setup() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  ss.setSpreadsheetLocale('zh_TW');
  buildStock_(ss);
  ss.setActiveSheet(ss.getSheetByName(SHEET_STOCK));
}

function buildStock_(ss) {
  var sh = ss.getSheetByName(SHEET_STOCK) || ss.insertSheet(SHEET_STOCK, 0);
  var headers = ['廠商名稱', '商品編號', '商品名稱', '可賣量', '成本', '售價'];
  sh.getRange(1, 1, 1, headers.length).setValues([headers])
    .setFontWeight('bold').setBackground('#263238').setFontColor('#ffffff');
  sh.setFrozenRows(1);

  sh.getRange('B2:B' + MAX_ROWS).setNumberFormat('@'); // 商品編號 20 碼保文字
  sh.getRange('D2:F' + MAX_ROWS).setNumberFormat('#,##0');
  sh.setColumnWidth(2, 190);  // 商品編號
  sh.setColumnWidth(3, 380);  // 商品名稱

  // 可賣量 = 0 整列標紅（缺貨一眼看出）
  var outOfStock = SpreadsheetApp.newConditionalFormatRule()
    .setRanges([sh.getRange('A2:F' + MAX_ROWS)])
    .whenFormulaSatisfied('=AND($B2<>"",$D2=0)')
    .setBackground('#fce4ec').setFontColor('#c62828')
    .build();
  sh.setConditionalFormatRules([outOfStock]);

  // 標題列篩選器（可依廠商/可賣量排序過濾）
  if (sh.getFilter()) sh.getFilter().remove();
  sh.getRange('A1:F' + MAX_ROWS).createFilter();
}

/**
 * Web App 寫入端點：本機 匯入轉換.py POST JSON {token, rows:[[六欄]...]} 過來，
 * 驗 token（存指令碼屬性 API_TOKEN，不進 git）後整份覆蓋「庫存表」資料列。
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
    if (last > 1) sh.getRange(2, 1, last - 1, 6).clearContent();
    if (rows.length) sh.getRange(2, 1, rows.length, 6).setValues(rows);
    out.ok = true;
    out.written = rows.length;
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
