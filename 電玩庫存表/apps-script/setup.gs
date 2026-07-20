/**
 * 電玩庫存表 — Google Sheet 建置腳本 v2
 *
 * v2（2026-07-20）：格式改為對接 PChome 廠商商品匯出檔的六欄：
 *   廠商名稱 | 商品編號 | 商品名稱 | 可賣量 | 成本 | 售價
 * 資料由本機 `匯入轉換.py` 轉成 TSV 進剪貼簿，貼到「庫存表」分頁 A1。
 *
 * 使用方式：
 *   1. 試算表 → 擴充功能 → Apps Script，貼上本檔全部內容
 *   2. 執行 setup（第一次會跳授權）
 *   3. 之後每次匯入：本機跑 匯入轉換.py → 到「庫存表」點 A1 → Ctrl+V
 *
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
