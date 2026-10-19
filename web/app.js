const state = { page: 1, total: 0, limit: 30, jobs: [], sort: "updated_at", direction: "desc" };
let jobsRequest = 0;
let citiesRequest = 0;
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const esc = (value = "") => String(value).replace(/[&<>"']/g, c => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c]));
const labels = { intern: "实习招聘", campus: "校园招聘", experienced: "社会招聘", new: "新增", updated: "更新", dropped: "下架", restored: "重新上线", success: "成功", partial: "部分成功", failed: "失败", running: "运行中" };

async function api(path, options) {
  if (window.BYTE_MONITOR_STATIC) return window.StaticData.api(path, options);
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "请求失败");
  return data;
}
function toast(message) {
  const el = $("#toast"); el.textContent = message; el.classList.add("show");
  clearTimeout(toast.timer); toast.timer = setTimeout(() => el.classList.remove("show"), 2800);
}
function fmt(value) { return value ? value.slice(0, 16) : "暂无"; }
function cityTags(job) {
  const cities = job.cities || (job.city ? job.city.split(/[,，]/).map(x => x.trim()).filter(Boolean) : []);
  return `<div class="city-tags">${cities.length ? cities.map(city => `<span class="city-tag">${esc(city)}</span>`).join("") : '<span class="cell-muted">城市未注明</span>'}</div>`;
}

async function loadCities() {
  const request = ++citiesRequest;
  const params = new URLSearchParams({ type: $("#type-filter").value, status: $("#status-filter").value });
  const data = await api(`/api/cities?${params}`);
  if (request !== citiesRequest) return;
  const select = $("#city-filter");
  const selected = select.value;
  const options = data.items.map(item => `<option value="${esc(item.city)}">${esc(item.city)}（${item.count}）</option>`);
  if (data.unknown_count) options.push(`<option value="__unknown__">城市未注明（${data.unknown_count}）</option>`);
  if (selected && !data.items.some(item => item.city === selected) && selected !== "__unknown__") {
    options.push(`<option value="${esc(selected)}">${esc(selected)}（0）</option>`);
  } else if (selected === "__unknown__" && !data.unknown_count) {
    options.push('<option value="__unknown__">城市未注明（0）</option>');
  }
  select.innerHTML = '<option value="">全部城市</option>' + options.join("");
  select.value = selected;
}

async function loadSummary() {
  const data = await api("/api/summary");
  $("#total-count").textContent = data.total.toLocaleString();
  $("#intern-count").textContent = data.types.intern.toLocaleString();
  $("#campus-count").textContent = data.types.campus.toLocaleString();
  $("#experienced-count").textContent = data.types.experienced.toLocaleString();
  $("#changed-count").textContent = data.changed7d.toLocaleString();
  $("#db-status").textContent = `${window.BYTE_MONITOR_STATIC ? "已更新" : "已连接"} · ${data.total.toLocaleString()} 条有效数据`;
  $("#last-run").textContent = data.last_run ? `最近同步 ${fmt(data.last_run.finished_at || data.last_run.started_at)}` : "尚无运行记录";
  const runButton = $("#run-now");
  runButton.disabled = data.running;
  runButton.textContent = window.BYTE_MONITOR_STATIC ? "采集记录" : (data.running ? "正在采集…" : "立即采集");
  const completedRun = !data.running && data.last_run?.finished_at ? data.last_run.id : null;
  if (completedRun && state.completedRun && completedRun !== state.completedRun) {
    await Promise.all([loadCities(), loadJobs()]);
  }
  if (completedRun) state.completedRun = completedRun;
}

async function loadJobs() {
  const request = ++jobsRequest;
  $("#jobs-body").innerHTML = `<tr><td colspan="8" class="cell-muted">正在读取本地数据库…</td></tr>`;
  const params = new URLSearchParams({ q: $("#search").value, type: $("#type-filter").value, city: $("#city-filter").value, status: $("#status-filter").value, page: state.page, limit: state.limit, sort: state.sort, direction: state.direction });
  const data = await api(`/api/jobs?${params}`);
  if (request !== jobsRequest) return;
  state.total = data.total; state.jobs = data.items;
  $("#result-count").textContent = `共 ${data.total.toLocaleString()} 条`;
  $("#page-info").textContent = `第 ${data.page} / ${Math.max(1, Math.ceil(data.total / data.limit))} 页`;
  $("#prev-page").disabled = state.page <= 1;
  $("#next-page").disabled = state.page * state.limit >= data.total;
  $("#empty-state").classList.toggle("hidden", data.items.length > 0);
  $("#jobs-body").innerHTML = data.items.map((job, index) => `
    <tr>
      <td class="job-title" data-index="${index}">${esc(job.job_name || job.title || "未命名职位")}</td>
      <td class="cell-muted">${esc(job.team_name || "未解析")}</td>
      <td><span class="tag">${labels[job.source_type] || esc(job.source_type)}</span></td>
      <td>${cityTags(job)}</td>
      <td class="cell-muted">${fmt(job.publish_time)}</td>
      <td class="cell-muted">${fmt(job.updated_at)}</td>
      <td><span class="tag ${job.is_active ? "" : "dropped"}">${job.is_active ? "有效" : "已下架"}</span></td>
      <td>${job.detail_url ? `<a class="job-link" href="${esc(job.detail_url)}" target="_blank" rel="noreferrer">查看原岗位</a>` : "暂无"}</td>
    </tr>`).join("");
}

function showJob(job) {
  const p = job.payload || {};
  $("#job-detail").innerHTML = `
    <div class="detail-head"><h2>${esc(job.job_name || job.title || "未命名职位")}</h2>
      <div class="detail-meta"><span class="tag">${labels[job.source_type]}</span>${cityTags(job)}<span class="tag ${job.is_active ? "" : "dropped"}">${job.is_active ? "有效" : "已下架"}</span></div>
    </div>
    <section class="detail-section"><h3>职位信息</h3><p>团队：${esc(job.team_name || "未解析")}\n部门：${esc(job.department || "未注明")}\n类别：${esc(job.category || "未注明")}\n发布时间：${esc(job.publish_time || "未注明")}\n采集时间：${esc(job.picked_at || "未注明")}</p></section>
    ${job.team_intro ? `<section class="detail-section"><h3>团队介绍</h3><p>${esc(job.team_intro)}</p></section>` : ""}
    <section class="detail-section"><h3>职位描述</h3><p>${esc(p.description || "暂无职位描述")}</p></section>
    <section class="detail-section"><h3>职位要求</h3><p>${esc(p.requirement || "暂无职位要求")}</p></section>
    ${job.detail_url ? `<section class="detail-section"><a class="primary" href="${esc(job.detail_url)}" target="_blank" rel="noreferrer">打开字节跳动职位页面</a></section>` : ""}`;
  $("#job-dialog").showModal();
}

async function loadChanges() {
  const data = await api("/api/changes?limit=60");
  $("#changes-list").innerHTML = data.items.length ? data.items.map(item => `
    <article class="change-item"><div><span class="tag ${item.change_type === "dropped" ? "dropped" : ""}">${labels[item.change_type] || esc(item.change_type)}</span></div>
      <div class="change-copy"><strong>${item.detail_url ? `<a class="change-title-link" href="${esc(item.detail_url)}" target="_blank" rel="noreferrer">${esc(item.job_name || item.title || "未命名职位")}</a>` : esc(item.job_name || item.title || "未命名职位")}</strong><span>${labels[item.source_type] || esc(item.source_type)} · ${esc(item.detail || "")}${formatChangedFields(item.changed_fields)}</span></div>
      ${item.detail_url ? `<a class="change-action" href="${esc(item.detail_url)}" target="_blank" rel="noreferrer">查看原岗位 ↗</a>` : `<span class="cell-muted">链接不可用</span>`}
      <time class="change-time">${fmt(item.created_at)}</time></article>`).join("") : `<div class="empty"><strong>暂无变化记录</strong><span>完成第一次采集后，数据变化会显示在这里。</span></div>`;
}
function formatChangedFields(value) {
  if (!value) return "";
  try {
    const fields = JSON.parse(value);
    return fields.length ? ` · 字段：${fields.join("、")}` : "";
  } catch { return ""; }
}
async function loadRuns() {
  const data = await api("/api/runs");
  $("#runs-body").innerHTML = data.items.map(run => `<tr><td>${fmt(run.started_at)}</td><td><span class="tag ${run.status}">${labels[run.status] || esc(run.status)}</span></td><td>${run.new_count}</td><td>${run.updated_count}</td><td>${run.dropped_count}</td><td class="cell-muted">${esc(run.message || "")}</td></tr>`).join("") || `<tr><td colspan="6" class="cell-muted">暂无运行记录</td></tr>`;
}
async function loadSchedule() {
  const s = await api("/api/schedule");
  $("#schedule-enabled").checked = s.enabled; $("#schedule-mode").value = s.mode;
  $("#schedule-time").value = s.time; $("#schedule-interval").value = s.interval_minutes;
  $$("#weekday-field input").forEach(input => input.checked = s.weekdays.includes(Number(input.value)));
  if (s.system_task) $("#save-feedback").textContent = s.system_task.message || "";
  syncScheduleFields();
}
async function loadNotifications() {
  const settings = await api("/api/notifications");
  $("#notify-changes").checked = settings.changes;
  $("#notify-failures").checked = settings.failures;
  $("#notify-success").checked = settings.success_without_changes;
}
function syncScheduleFields() {
  const mode = $("#schedule-mode").value;
  $("#time-field").classList.toggle("hidden", mode === "interval");
  $("#interval-field").classList.toggle("hidden", mode !== "interval");
  $("#weekday-field").classList.toggle("hidden", mode !== "weekly");
}
function switchView(name) {
  $$(".nav-item").forEach(el => el.classList.toggle("active", el.dataset.view === name));
  $$(".view").forEach(el => el.classList.remove("active"));
  $(`#${name}-view`).classList.add("active");
  $("#page-title").textContent = { jobs:"职位浏览", changes:"变化记录", runs:"运行历史", settings:"定时设置" }[name];
  $("#summary").classList.toggle("hidden", name === "settings");
  if (name === "changes") loadChanges(); if (name === "runs") loadRuns(); if (name === "settings") { loadSchedule(); loadNotifications(); }
}

$$(".nav-item").forEach(el => el.addEventListener("click", () => switchView(el.dataset.view)));
let searchTimer;
$("#search").addEventListener("input", () => { clearTimeout(searchTimer); searchTimer = setTimeout(() => { state.page = 1; loadJobs(); }, 250); });
["type-filter","status-filter"].forEach(id => $(`#${id}`).addEventListener("change", () => {
  state.page = 1;
  Promise.all([loadCities(), loadJobs()]).catch(error => toast(error.message));
}));
$("#city-filter").addEventListener("change", () => { state.page = 1; loadJobs().catch(error => toast(error.message)); });
function syncSortControls() {
  $("#sort-field").value = state.sort;
  $("#sort-direction").value = state.direction;
  $$(".sort-button").forEach(item => {
    item.classList.toggle("active", item.dataset.sort === state.sort);
    item.querySelector("span")?.remove();
    if (item.dataset.sort === state.sort) item.insertAdjacentHTML("beforeend", `<span>${state.direction === "asc" ? "↑" : "↓"}</span>`);
  });
}
["sort-field","sort-direction"].forEach(id => $(`#${id}`).addEventListener("change", () => {
  state.sort = $("#sort-field").value;
  state.direction = $("#sort-direction").value;
  state.page = 1;
  syncSortControls();
  loadJobs();
}));
$$(".sort-button").forEach(button => button.addEventListener("click", () => {
  const nextSort = button.dataset.sort;
  if (state.sort === nextSort) state.direction = state.direction === "asc" ? "desc" : "asc";
  else { state.sort = nextSort; state.direction = "asc"; }
  state.page = 1;
  syncSortControls();
  loadJobs();
}));
$("#prev-page").addEventListener("click", () => { state.page--; loadJobs(); });
$("#next-page").addEventListener("click", () => { state.page++; loadJobs(); });
$("#jobs-body").addEventListener("click", e => { const cell = e.target.closest("[data-index]"); if (cell) showJob(state.jobs[Number(cell.dataset.index)]); });
$(".dialog-close").addEventListener("click", () => $("#job-dialog").close());
$("#job-dialog").addEventListener("click", e => { if (e.target === $("#job-dialog")) $("#job-dialog").close(); });
$("#run-now").addEventListener("click", async () => {
  if (window.BYTE_MONITOR_STATIC) {
    window.open(`https://github.com/${window.BYTE_MONITOR_STATIC.repository}/actions/workflows/monitor.yml`, "_blank", "noopener");
    return;
  }
  try { await api("/api/run", { method:"POST" }); toast("采集任务已启动，可在“运行历史”查看进度"); loadSummary(); }
  catch (error) { toast(error.message === "请求失败" ? "已有采集任务正在运行" : error.message); }
});
$("#schedule-mode").addEventListener("change", syncScheduleFields);
$("#schedule-form").addEventListener("submit", async e => {
  e.preventDefault();
  const schedule = { enabled: $("#schedule-enabled").checked, mode: $("#schedule-mode").value, time: $("#schedule-time").value, interval_minutes: Number($("#schedule-interval").value), weekdays: $$("#weekday-field input:checked").map(x => Number(x.value)) };
  await api("/api/schedule", { method:"POST", headers:{ "Content-Type":"application/json" }, body:JSON.stringify(schedule) });
  $("#save-feedback").textContent = "计划已保存并生效"; toast("定时采集计划已保存");
});
$("#test-notification").addEventListener("click", async () => {
  try {
    await api("/api/notification/test", { method:"POST" });
    toast("测试通知已发送，请查看 Windows 弹窗");
  } catch (error) { toast(`通知发送失败：${error.message}`); }
});
$("#notification-form").addEventListener("submit", async e => {
  e.preventDefault();
  await api("/api/notifications", { method:"POST", headers:{ "Content-Type":"application/json" }, body:JSON.stringify({
    changes: $("#notify-changes").checked,
    failures: $("#notify-failures").checked,
    success_without_changes: $("#notify-success").checked
  })});
  toast("通知策略已保存");
});
async function exportData(format) {
  try {
    const result = await api("/api/export", { method:"POST", headers:{ "Content-Type":"application/json" }, body:JSON.stringify({ format }) });
    toast(`已导出到 ${result.name}`);
  } catch (error) { toast(`导出失败：${error.message}`); }
}
$("#export-xlsx").addEventListener("click", () => exportData("xlsx"));
$("#export-json").addEventListener("click", () => exportData("json"));

syncSortControls();
window.StaticData?.initialize();
Promise.all([loadSummary(), loadCities(), loadJobs()]).catch(error => toast(error.message));
setInterval(() => loadSummary().catch(error => toast(error.message)), 10000);
