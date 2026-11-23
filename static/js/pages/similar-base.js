/*
 * เสนอรหัส/ชื่อที่ "คล้าย" กับที่กำลังคีย์ ในหน้าเพิ่ม / แก้ไขข้อมูลพื้นฐาน (createBase* / editBase*)
 * ให้ user ตรวจก่อนบันทึก กันการเพิ่มข้อมูลซ้ำ  ฝั่ง server ดู weightapp/views_similar_base.py
 * หน้าตาอยู่ที่ static/css/similar-base.css
 *
 * ใช้: initSimilarBase({url: '/searchSimilarBase/', detailUrl: '/similarBaseDetail/', model: 'BaseCustomer', input: '#id_customer_name'})
 * ปุ่ม "ดูข้อมูล" เปิด popup อ่านอย่างเดียว (ไม่มีปุ่มบันทึก) ข้อมูลจาก similarBaseDetail
 * ไม่พึ่ง jQuery เพราะแต่ละหน้าโหลด jQuery คนละรุ่น/คนละที่
 */
(function () {
  'use strict';

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text; // textContent กัน XSS จากชื่อในฐานข้อมูล
    return node;
  }

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  // ไฮไลต์ส่วนของชื่อที่ตรงกับคำที่คีย์ (สร้าง node เอง ไม่ใช้ innerHTML)
  function highlightName(target, name, query) {
    var at = query ? name.toLowerCase().indexOf(query.toLowerCase()) : -1;
    if (at < 0) {
      target.appendChild(document.createTextNode(name));
      return;
    }
    target.appendChild(document.createTextNode(name.slice(0, at)));
    target.appendChild(el('mark', '', name.slice(at, at + query.length)));
    target.appendChild(document.createTextNode(name.slice(at + query.length)));
  }

  /* ---------- popup ดูข้อมูล (อ่านอย่างเดียว) ---------- */
  var detailOpts = null;   // {url, model} จาก initSimilarBase
  var popup = null;        // {overlay, card, returnFocus}

  function closeDetail() {
    if (!popup) return;
    popup.overlay.remove();
    document.removeEventListener('keydown', onPopupKey);
    if (popup.returnFocus) popup.returnFocus.focus();
    popup = null;
  }

  function onPopupKey(e) {
    if (e.key === 'Escape') closeDetail();
  }

  function popupShell(returnFocus) {
    closeDetail();
    var overlay = el('div', 'sbd-overlay');
    var card = el('div', 'sbd-card');
    card.setAttribute('role', 'dialog');
    card.setAttribute('aria-modal', 'true');
    card.setAttribute('aria-label', 'ดูข้อมูล');
    card.tabIndex = -1;
    overlay.appendChild(card);
    overlay.addEventListener('click', function (e) { if (e.target === overlay) closeDetail(); });
    document.addEventListener('keydown', onPopupKey);
    document.body.appendChild(overlay);
    popup = { overlay: overlay, card: card, returnFocus: returnFocus };
    return card;
  }

  function popupMessage(card, text) {
    clear(card);
    card.appendChild(el('div', 'sbd-loading', text));
  }

  function renderDetail(card, d) {
    clear(card);
    var head = el('div', 'sbd-head');
    head.appendChild(el('span', 'sb-code', d.id));
    var title = el('div', 'sbd-title', d.name || '-');
    if (d.disabled) title.appendChild(el('span', 'sb-tag sb-tag-off', 'ปิดการใช้งาน'));
    head.appendChild(title);
    var close = el('button', 'sb-close');
    close.type = 'button';
    close.setAttribute('aria-label', 'ปิด');
    close.appendChild(el('i', 'bi bi-x-lg'));
    close.addEventListener('click', closeDetail);
    head.appendChild(close);
    card.appendChild(head);

    var fields = el('dl', 'sbd-fields');
    (d.fields || []).forEach(function (f) {
      var dt = el('dt', '', f.label);
      if (f.required) dt.appendChild(el('span', 'text-danger', ' *'));
      fields.appendChild(dt);
      fields.appendChild(el('dd', f.value === '-' ? 'sbd-empty' : '', f.value));
    });
    card.appendChild(fields);

    var usage = el('div', 'sbd-usage');
    if (d.usage && d.usage.length) {
      usage.appendChild(el('div', 'sbd-usage-title', 'ใช้ในตาชั่งแล้ว ' + d.usage.length + ' บริษัท'));
      var chips = el('div', 'sbd-usage-list');
      d.usage.forEach(function (u) {
        var chip = el('span', 'sbd-usage-chip');
        chip.appendChild(el('b', '', u.code));
        chip.appendChild(document.createTextNode(' ' + u.name + ' · ' + u.count.toLocaleString() + ' รายการ'));
        chips.appendChild(chip);
      });
      usage.appendChild(chips);
    } else {
      usage.appendChild(el('div', 'sbd-usage-title sbd-empty', 'ยังไม่มีบริษัทใดใช้ข้อมูลนี้ในตาชั่ง'));
    }
    card.appendChild(usage);

    var foot = el('div', 'sbd-foot');
    foot.appendChild(el('span', 'sbd-readonly', 'ดูอย่างเดียว ไม่สามารถแก้ไขได้'));
    var full = el('a', 'sbd-full');
    full.href = d.view_url;
    full.target = '_blank';
    full.rel = 'noopener';
    full.appendChild(el('i', 'bi bi-box-arrow-up-right'));
    full.appendChild(el('span', '', 'เปิดหน้าเต็ม'));
    foot.appendChild(full);
    card.appendChild(foot);
    close.focus();
  }

  function openDetail(id, returnFocus) {
    if (!detailOpts) return;
    var card = popupShell(returnFocus);
    popupMessage(card, 'กำลังโหลดข้อมูล…');
    var url = detailOpts.url + '?model=' + encodeURIComponent(detailOpts.model) + '&id=' + encodeURIComponent(id);
    fetch(url, { credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (res) { if (!res.ok) throw new Error(res.status); return res.json(); })
      .then(function (d) { if (popup && popup.card === card) renderDetail(card, d); })
      .catch(function () { if (popup && popup.card === card) popupMessage(card, 'โหลดข้อมูลไม่สำเร็จ ลองใหม่อีกครั้ง'); });
  }

  function buildItem(r, query) {
    var li = el('li', 'sb-item');
    li.appendChild(el('span', 'sb-code', r.id));

    var name = el('div', 'sb-name');
    // ชื่ออยู่ใน span ของตัวเอง (.sb-name เป็น flex เรียง ชื่อ / ป้าย / ค่าช่องบังคับ ในแถวเดียวกัน)
    var nameText = el('span', 'sb-name-text');
    highlightName(nameText, r.name || '-', query);
    name.appendChild(nameText);
    if (r.exact) name.appendChild(el('span', 'sb-tag sb-tag-exact', 'ชื่อตรงกัน'));
    else if (r.sound_alike) name.appendChild(el('span', 'sb-tag sb-tag-alike', 'สะกดต่าง'));
    if (r.disabled) name.appendChild(el('span', 'sb-tag sb-tag-off', 'ปิดการใช้งาน'));
    // ค่าช่องบังคับกรอก (ประเภทเครื่องชั่ง / บริษัท / ทีม ...) ช่วยแยกว่าชื่อซ้ำแต่คนละประเภทหรือไม่
    if (r.details && r.details.length) {
      var details = el('div', 'sb-details');
      r.details.forEach(function (d) {
        var chip = el('span', 'sb-detail' + (d.value === '-' ? ' sb-detail-empty' : ''));
        chip.appendChild(el('span', 'sb-detail-label', d.label));
        chip.appendChild(el('span', 'sb-detail-value', d.value));
        details.appendChild(chip);
      });
      li.appendChild(name);
      li.appendChild(details); // คอลัมน์ของตัวเอง ต่อจากชื่อ ในแถวเดียวกับรหัส
    } else {
      li.appendChild(name);
    }

    var pct = Math.round((r.score || 0) * 100);
    var score = el('div', 'sb-score', 'คล้าย ' + pct + '%');
    var bar = el('div', 'sb-bar');
    var fill = el('span');
    fill.style.width = pct + '%';
    bar.appendChild(fill);
    score.appendChild(bar);
    li.appendChild(score);

    // ดูข้อมูลใน popup เล็ก (อ่านอย่างเดียว) ไม่ต้องออกจากหน้าที่กำลังกรอก
    var btn = el('button', 'sb-view');
    btn.type = 'button';
    btn.title = 'ดูข้อมูลนี้';
    btn.appendChild(el('i', 'bi bi-eye'));
    btn.appendChild(el('span', 'sb-view-text', 'ดูข้อมูล'));
    btn.addEventListener('click', function () { openDetail(r.id, btn); });
    li.appendChild(btn);
    return li;
  }

  // blocked = ชื่อตรงกับข้อมูลที่มีอยู่ บันทึกไม่ได้ (หน้าแก้ไขที่ยังไม่เปลี่ยนชื่อ = false แม้ชื่อตรงกัน)
  function render(box, results, query, onClose, blocked) {
    clear(box);
    if (!results.length) {
      box.hidden = true;
      return;
    }
    var hasExact = results.some(function (r) { return r.exact; });
    box.className = 'sb-box' + (hasExact ? ' sb-exact' : '');

    var head = el('div', 'sb-head');
    head.appendChild(el('i', 'sb-head-icon bi ' + (hasExact ? 'bi-exclamation-octagon-fill' : 'bi-exclamation-triangle-fill')));
    var text = el('div', 'sb-head-text');
    text.appendChild(el('div', 'sb-title',
      hasExact ? 'มีข้อมูลชื่อนี้อยู่แล้วในระบบ' : 'พบข้อมูลที่คล้ายกัน ' + results.length + ' รายการ'));
    text.appendChild(el('div', 'sb-sub',
      blocked ? 'ไม่สามารถบันทึกได้ กรุณาใช้ข้อมูลเดิม หรือเปลี่ยนชื่อ'
        : hasExact ? 'ชื่อนี้ซ้ำกับข้อมูลอื่นที่มีอยู่เดิม (ยังไม่ได้เปลี่ยนชื่อ จึงบันทึกได้)'
        : 'กรุณาตรวจสอบว่าไม่ใช่ข้อมูลเดียวกัน ก่อนเพิ่มใหม่'));
    head.appendChild(text);
    var close = el('button', 'sb-close');
    close.type = 'button';
    close.title = 'ซ่อน';
    close.setAttribute('aria-label', 'ซ่อน');
    close.appendChild(el('i', 'bi bi-x-lg'));
    close.addEventListener('click', onClose);
    head.appendChild(close);
    box.appendChild(head);

    var list = el('ul', 'sb-list');
    results.forEach(function (r) { list.appendChild(buildItem(r, query)); });
    box.appendChild(list);
    box.hidden = false;
  }

  window.initSimilarBase = function (opts) {
    var input = document.querySelector(opts.input);
    if (!input || !opts.url || !opts.model) return;
    detailOpts = opts.detailUrl ? { url: opts.detailUrl, model: opts.model } : null;

    var box = el('div', 'sb-box');
    box.hidden = true;
    box.setAttribute('role', 'status');
    box.setAttribute('aria-live', 'polite');
    input.insertAdjacentElement('afterend', box);

    var timer = null;
    var lastQuery = null;
    var seq = 0; // ทิ้งผลของ request เก่าที่ตอบกลับช้ากว่า request ใหม่

    function hide() {
      box.hidden = true; // ซ่อนจนกว่าจะคีย์ชื่อใหม่ (ถ้าชื่อตรงกัน ปุ่มบันทึกยังปิดอยู่)
    }

    // ---- ชื่อตรงกับข้อมูลที่มีอยู่ -> ปิดปุ่มบันทึก (server ตรวจซ้ำอีกชั้นใน NoExactDuplicateNameMixin) ----
    var form = input.form;
    var saveButtons = form ? Array.prototype.slice.call(
      form.querySelectorAll('button[type="submit"], input[type="submit"]')) : [];
    var blocked = false;

    function squash(text) { return (text || '').toLowerCase().replace(/[\s.,\-()\/\\'"&_:;]+/g, ''); }
    // หน้าแก้ไขที่ยังไม่เปลี่ยนชื่อ : ข้อมูลเก่าที่ชื่อซ้ำอยู่แล้ว ยังแก้ช่องอื่นแล้วบันทึกได้
    function nameUnchanged() { return !!opts.exclude && squash(input.value) === squash(input.defaultValue); }

    function setBlocked(value) {
      blocked = value;
      saveButtons.forEach(function (btn) {
        btn.disabled = value;
        btn.title = value ? 'มีข้อมูลชื่อนี้อยู่แล้วในระบบ ไม่สามารถบันทึกได้' : '';
      });
    }

    function show(results, query) {
      var exact = results.some(function (r) { return r.exact; });
      var block = exact && !nameUnchanged();
      setBlocked(block);
      render(box, results, query, hide, block);
    }

    if (form) {
      form.addEventListener('submit', function (e) {
        if (!blocked) return;
        e.preventDefault();
        box.hidden = false;
        input.focus();
      });
    }

    function search() {
      var query = input.value.trim();
      if (query === lastQuery) return;
      lastQuery = query;
      if (query.length < 2) {
        show([], query);
        return;
      }
      var mySeq = ++seq;
      var url = opts.url + '?model=' + encodeURIComponent(opts.model) + '&q=' + encodeURIComponent(query);
      if (opts.exclude) url += '&exclude=' + encodeURIComponent(opts.exclude); // หน้าแก้ไข : ไม่เสนอตัวเอง
      fetch(url, { credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function (res) { return res.ok ? res.json() : { results: [] }; })
        .then(function (data) { if (mySeq === seq) show(data.results || [], query); })
        .catch(function () { if (mySeq === seq) show([], query); });
    }

    input.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(search, 350);
    });
    input.addEventListener('blur', search);
    // ฟอร์มถูกส่งกลับมาพร้อม error ยังมีชื่อเดิมค้างอยู่ ให้เช็คทันที
    if (input.value.trim()) search();
  };
})();
