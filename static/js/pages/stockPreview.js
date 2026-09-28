////// start toggle ย่อ/ขยาย การ์ดชนิดหินใน stock //////
//ไม่ใช้ data-bs-toggle เพราะหน้านี้โหลด Bootstrap Collapse ซ้อนกัน 2 ชุด (จาก app.js และ CDN)
//ทำให้ toggle ทำงานแค่ทิศทางเดียว จึงคุมเองด้วย class "show" ตรงๆ แทน
$(document).on('click', '.stock-ssn-toggle-btn', function () {
  var $btn = $(this);
  var $target = $($btn.data('collapse-target'));
  if ($target.length === 0) {
    return;
  }

  var expanded = $btn.attr('aria-expanded') === 'true';
  $target.toggleClass('show', !expanded);
  $btn.attr('aria-expanded', !expanded);
});
////// end toggle ย่อ/ขยาย การ์ดชนิดหินใน stock //////

////// start preview ยอด stock รายเดือนตามชนิดหิน (คำนวณล่วงหน้าก่อนบันทึกจริง) //////
var stockPreviewTimer = null;

function initStockPreview(options) {
  options = options || {};
  var sourceSelector = options.sourceSelector || '.source';
  var quantitySelector = options.quantitySelector || '.quantity';
  var createdSelector = options.createdSelector || '#id_created';
  var stoneSelector = options.stoneSelector || '#id_stone';
  var companySelector = options.companySelector || '#id_company';
  var containerSelector = options.containerSelector || '#stock-preview-container';
  var formCardSelector = options.formCardSelector || '#stock-form-card';
  var previewColSelector = options.previewColSelector || '#stock-preview-col';
  var formColSelector = options.formColSelector || '#stock-form-col';

  //ตอนโหลดหน้าให้เห็นแค่ form เต็มความกว้างก่อน พอมี preview (เลือกชนิดหินแล้ว) ค่อยแบ่งคอลัมน์ซ้าย-ขวา
  function setPreviewColumnVisible(visible) {
    var $previewCol = $(previewColSelector);
    var $formCol = $(formColSelector);

    if (visible) {
      $previewCol.removeClass('d-none');
      $formCol.removeClass('col-12').addClass('col-md-8 col-12');
    } else {
      $previewCol.addClass('d-none');
      $formCol.removeClass('col-md-8 col-12').addClass('col-12');
    }
  }

  //ให้ preview สูงเท่า form ที่อยู่ข้างๆ ถ้า preview สูงกว่าให้ scroll แทนการดันความสูงลงมา
  function syncPreviewHeight() {
    var $container = $(containerSelector);
    var $formCard = $(formCardSelector);

    if ($(window).width() < 768 || $formCard.length === 0 || $container.hasClass('d-none')) {
      $container.css('height', '');
      return;
    }

    $container.css('height', $formCard.outerHeight() + 'px');
  }

  //เลื่อน scroll bar ของตาราง preview ไปที่แถววันที่กำลังแก้ไข/เพิ่ม
  function scrollToTargetRow($container) {
    var $wrap = $container.find('.stock-preview-table-wrap');
    var $target = $container.find('.stock-preview-target').first();
    if ($wrap.length === 0 || $target.length === 0) {
      return;
    }

    var wrapEl = $wrap[0];
    var targetEl = $target[0];
    var wrapRect = wrapEl.getBoundingClientRect();
    var targetRect = targetEl.getBoundingClientRect();
    var headerHeight = $wrap.find('thead').outerHeight() || 0;

    var offsetWithinWrap = (targetRect.top - wrapRect.top) + wrapEl.scrollTop;
    var scrollTop = offsetWithinWrap - headerHeight - (wrapEl.clientHeight / 2) + (targetEl.offsetHeight / 2);
    wrapEl.scrollTop = Math.max(scrollTop, 0);
  }

  function collectSubmittedItems() {
    var items = [];
    $(sourceSelector).each(function (index) {
      var sourceVal = $(this).val();
      var quantityVal = $(quantitySelector).eq(index).val();
      if (sourceVal) {
        items.push({ source: sourceVal, quantity: quantityVal || 0 });
      }
    });
    return items;
  }

  function escapeHtml(value) {
    return $('<div>').text(value == null ? '' : value).html();
  }

  function formatQty(value) {
    return Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  //แปลงวันที่จาก YYYY-MM-DD (ที่ backend ส่งมา) เป็น dd/MM/YYYY
  function formatDate(isoDate) {
    var parts = String(isoDate).split('-');
    if (parts.length !== 3) {
      return isoDate;
    }
    return parts[2] + '/' + parts[1] + '/' + parts[0];
  }

  function renderStockPreview(data) {
    var $container = $(containerSelector);

    if (!data.days || data.days.length === 0) {
      $container.addClass('d-none').css('height', '').html('');
      setPreviewColumnVisible(false);
      return;
    }

    var rowsHtml = '';
    $.each(data.days, function (i, day) {
      var rowClasses = [];
      if (day.is_target) { rowClasses.push('stock-preview-target'); }
      if (day.warning) { rowClasses.push('stock-preview-negative'); }

      rowsHtml += '<tr class="' + rowClasses.join(' ') + '">' +
        '<td>' + escapeHtml(formatDate(day.date)) +
        (day.is_target ? ' <span class="badge bg-primary">กำลังแก้ไข</span>' : '') +
        (day.warning ? ' <span class="badge bg-danger"><i class="bi bi-exclamation-triangle-fill"></i> ติดลบ</span>' : '') +
        '</td>' +
        '<td class="text-end stock-preview-total">' + formatQty(day.total) + '</td>' +
        '</tr>';
    });

    var warningHtml = data.has_warning
      ? '<div class="alert alert-danger py-2 stock-preview-alert mb-0"><i class="bi bi-exclamation-triangle-fill"></i> คำเตือน: มีบางวันในเดือนนี้ที่ยอด stock ติดลบ หากบันทึกค่านี้</div>'
      : '';

    var html =
      '<div class="stock-preview-card">' +
        '<div class="stock-preview-header">' +
          '<h5><i class="bi bi-graph-up-arrow"></i> ตัวอย่างยอด stock เดือนนี้ : ' + escapeHtml(data.stone_name) + '</h5>' +
        '</div>' +
        warningHtml +
        '<div class="stock-preview-table-wrap">' +
          '<table class="table stock-preview-table">' +
            '<thead><tr><th>วันที่</th><th class="text-end">ยอด stock (ตัน)</th></tr></thead>' +
            '<tbody>' + rowsHtml + '</tbody>' +
          '</table>' +
        '</div>' +
      '</div>';

    setPreviewColumnVisible(true);
    $container.removeClass('d-none').html(html);
    syncPreviewHeight();
    scrollToTargetRow($container);
  }

  function requestStockPreview() {
    var created = $(createdSelector).val();
    var company = $(companySelector).val();
    var stone = $(stoneSelector).val();

    if (!created || !company || !stone) {
      $(containerSelector).addClass('d-none').css('height', '').html('');
      setPreviewColumnVisible(false);
      return;
    }

    $.ajax({
      url: window.previewStockInMonthUrl,
      data: {
        created: created,
        company: company,
        stone: stone,
        'source[]': $.map(collectSubmittedItems(), function (it) { return it.source; }),
        'quantity[]': $.map(collectSubmittedItems(), function (it) { return it.quantity; }),
      },
      traditional: true,
      dataType: 'json',
      success: function (data) {
        renderStockPreview(data);
      }
    });
  }

  function scheduleStockPreview() {
    clearTimeout(stockPreviewTimer);
    stockPreviewTimer = setTimeout(requestStockPreview, 300);
  }

  $(document).on('change keyup', sourceSelector + ', ' + quantitySelector, scheduleStockPreview);
  $(stoneSelector + ', ' + createdSelector).on('change', scheduleStockPreview);

  var resizeTimer = null;
  $(window).on('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(syncPreviewHeight, 150);
  });

  //เริ่มต้นให้เห็นแค่ form ก่อน (กันหน้ากระพริบระหว่างรอ ajax แรก)
  setPreviewColumnVisible(false);
  scheduleStockPreview();
}
////// end preview ยอด stock รายเดือนตามชนิดหิน //////
