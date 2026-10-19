/* GitHub Pages 数据适配器：浏览操作在本地公开快照中完成，不使用账号凭据。 */
window.StaticData = (() => {
  const config = window.BYTE_MONITOR_STATIC;
  let snapshotPromise;
  const compare = new Intl.Collator("zh-CN", { numeric: true });
  async function snapshot() {
    if (!snapshotPromise) snapshotPromise = (async () => {
      const response = await fetch(new URL("./data/monitor.json.gz", location.href), { cache: "no-cache" });
      if (!response.ok) throw new Error("数据快照加载失败");
      const stream = response.body.pipeThrough(new DecompressionStream("gzip"));
      return new Response(stream).json();
    })().catch(error => { snapshotPromise = null; throw error; });
    return snapshotPromise;
  }
  function filtered(jobs, params, includeCity = true) {
    const type = params.get("type") || "all";
    const status = params.get("status") || "active";
    const city = includeCity ? params.get("city") : "";
    const q = (params.get("q") || "").trim().toLocaleLowerCase();
    return jobs.filter(job => (type === "all" || job.source_type === type)
      && (status === "all" || Boolean(job.is_active) === (status === "active"))
      && (!city || (city === "__unknown__" ? !job.cities.length : job.cities.includes(city)))
      && (!q || [job.title, job.job_name, job.team_name, job.team_intro, job.city, job.department, job.category].some(value => String(value || "").toLocaleLowerCase().includes(q))));
  }
  function download(jobs, format) {
    const fields = ["job_name", "team_name", "city", "source_type", "publish_time", "updated_at", "is_active", "detail_url"];
    const csvCell = value => {
      let text = String(value ?? "");
      if (/^[=+@-]/.test(text)) text = "'" + text;
      return '"' + text.replaceAll('"', '""') + '"';
    };
    const isJson = format === "json";
    const content = isJson ? JSON.stringify(jobs, null, 2) : "\uFEFF" + [fields, ...jobs.map(job => fields.map(field => job[field]))].map(row => row.map(csvCell).join(",")).join("\r\n");
    const name = `jobs-${new Date().toISOString().slice(0,10)}.${isJson ? "json" : "csv"}`;
    const url = URL.createObjectURL(new Blob([content], { type: isJson ? "application/json" : "text/csv;charset=utf-8" }));
    const link = document.createElement("a"); link.href = url; link.download = name; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    return { path: name, name };
  }
  async function api(path, options) {
    const data = await snapshot();
    const url = new URL(path, location.origin);
    const params = url.searchParams;
    if (url.pathname === "/api/summary") {
      const active = data.jobs.filter(job => job.is_active);
      const types = { intern: 0, campus: 0, experienced: 0 };
      active.forEach(job => types[job.source_type]++);
      const cutoff = new Date(Date.now() - 7 * 864e5);
      return { total: active.length, types, changed7d: data.changes.filter(change => new Date(change.created_at.replace(" ", "T") + "+08:00") >= cutoff).length, last_run: data.runs[0] || { id: "seed", finished_at: data.generated_at }, running: false };
    }
    if (url.pathname === "/api/jobs") {
      const allowed = ["job_name", "team_name", "source_type", "city", "publish_time", "updated_at", "is_active"];
      const field = allowed.includes(params.get("sort")) ? params.get("sort") : "updated_at";
      const direction = params.get("direction") === "asc" ? 1 : -1;
      const jobs = filtered(data.jobs, params).sort((a,b) => direction * compare.compare(String(a[field] ?? ""), String(b[field] ?? "")) || compare.compare(a.job_key,b.job_key));
      const page = Math.max(1, Number(params.get("page")) || 1), limit = Math.min(100, Math.max(10, Number(params.get("limit")) || 30));
      return { items: jobs.slice((page-1)*limit, page*limit), total: jobs.length, page, limit };
    }
    if (url.pathname === "/api/cities") {
      const counts = new Map(); let unknown_count = 0;
      filtered(data.jobs, params, false).forEach(job => {
        if (!job.cities.length) unknown_count++;
        job.cities.forEach(city => counts.set(city, (counts.get(city) || 0) + 1));
      });
      return { items: [...counts].map(([city,count]) => ({ city,count })).sort((a,b) => compare.compare(a.city,b.city)), unknown_count };
    }
    if (url.pathname === "/api/changes") {
      const byKey = new Map(data.jobs.map(job => [job.job_key,job]));
      return { items: data.changes.slice(0, Number(params.get("limit")) || 60).map(change => ({ ...change, detail_url: byKey.get(change.job_key)?.detail_url, job_name: byKey.get(change.job_key)?.job_name })) };
    }
    if (url.pathname === "/api/runs") return { items: data.runs };
    if (url.pathname === "/api/status") return { running: false };
    if (url.pathname === "/api/export") return download(data.jobs, JSON.parse(options?.body || "{}").format);
    throw new Error("请在 GitHub Actions 中管理自动采集");
  }
  function initialize() {
    if (!config) return;
    document.querySelector('.nav-item[data-view="settings"]').hidden = true;
    document.querySelector(".sidebar-foot strong").textContent = "GitHub 数据快照";
    document.querySelector("#export-xlsx").textContent = "导出 CSV";
    document.querySelector("#run-now").title = config.schedule + "，点击查看或手动运行 Actions";
  }
  return { api, initialize };
})();
