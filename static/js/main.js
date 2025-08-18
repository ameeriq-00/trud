/**
 * TRUD - HelloCallers Proxy
 * JavaScript الرئيسي للواجهة الإدارية
 */

// الإعدادات العامة
const API_CONFIG = {
  baseURL: "/api/v1",
  apiKey: "trud-admin-key-12345",
  timeout: 30000,
};

// المساعدات العامة
class APIClient {
  constructor() {
    this.baseURL = API_CONFIG.baseURL;
    this.apiKey = API_CONFIG.apiKey;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const defaultOptions = {
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        "Content-Type": "application/json",
      },
      timeout: API_CONFIG.timeout,
    };

    const finalOptions = { ...defaultOptions, ...options };

    if (finalOptions.body && typeof finalOptions.body === "object") {
      finalOptions.body = JSON.stringify(finalOptions.body);
    }

    try {
      const response = await fetch(url, finalOptions);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        return await response.json();
      }

      return await response.text();
    } catch (error) {
      console.error("API Request failed:", error);
      throw error;
    }
  }

  async get(endpoint) {
    return this.request(endpoint, { method: "GET" });
  }

  async post(endpoint, data) {
    return this.request(endpoint, {
      method: "POST",
      body: data,
    });
  }

  async put(endpoint, data) {
    return this.request(endpoint, {
      method: "PUT",
      body: data,
    });
  }

  async delete(endpoint) {
    return this.request(endpoint, { method: "DELETE" });
  }
}

// إنشاء عميل API
const api = new APIClient();

// فئة إدارة الإشعارات
class NotificationManager {
  constructor() {
    this.container = this.createContainer();
  }

  createContainer() {
    let container = document.getElementById("notification-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "notification-container";
      container.className = "position-fixed top-0 end-0 p-3";
      container.style.zIndex = "9999";
      document.body.appendChild(container);
    }
    return container;
  }

  show(message, type = "info", duration = 5000) {
    const alertElement = document.createElement("div");
    alertElement.className = `alert alert-${type} alert-dismissible fade show`;
    alertElement.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

    this.container.appendChild(alertElement);

    // إزالة تلقائية
    setTimeout(() => {
      if (alertElement.parentNode) {
        alertElement.remove();
      }
    }, duration);

    return alertElement;
  }

  success(message, duration = 3000) {
    return this.show(message, "success", duration);
  }

  error(message, duration = 7000) {
    return this.show(message, "danger", duration);
  }

  warning(message, duration = 5000) {
    return this.show(message, "warning", duration);
  }

  info(message, duration = 4000) {
    return this.show(message, "info", duration);
  }
}

// إنشاء مدير الإشعارات
const notifications = new NotificationManager();

// فئة إدارة النماذج
class FormManager {
  static serialize(form) {
    const formData = new FormData(form);
    const data = {};

    for (let [key, value] of formData.entries()) {
      if (data[key]) {
        if (Array.isArray(data[key])) {
          data[key].push(value);
        } else {
          data[key] = [data[key], value];
        }
      } else {
        data[key] = value;
      }
    }

    return data;
  }

  static validate(form, rules = {}) {
    const errors = [];
    const data = this.serialize(form);

    for (let field in rules) {
      const rule = rules[field];
      const value = data[field];

      if (rule.required && (!value || value.trim() === "")) {
        errors.push(`${rule.label || field} مطلوب`);
        continue;
      }

      if (value && rule.pattern && !rule.pattern.test(value)) {
        errors.push(`${rule.label || field} غير صالح`);
      }

      if (value && rule.minLength && value.length < rule.minLength) {
        errors.push(
          `${rule.label || field} يجب أن يكون ${rule.minLength} أحرف على الأقل`
        );
      }

      if (value && rule.maxLength && value.length > rule.maxLength) {
        errors.push(
          `${rule.label || field} يجب أن يكون ${rule.maxLength} أحرف كحد أقصى`
        );
      }
    }

    return {
      valid: errors.length === 0,
      errors: errors,
      data: data,
    };
  }

  static showErrors(form, errors) {
    // إزالة الأخطاء السابقة
    form.querySelectorAll(".invalid-feedback").forEach((el) => el.remove());
    form
      .querySelectorAll(".is-invalid")
      .forEach((el) => el.classList.remove("is-invalid"));

    // عرض الأخطاء الجديدة
    errors.forEach((error) => {
      const errorDiv = document.createElement("div");
      errorDiv.className = "invalid-feedback d-block";
      errorDiv.textContent = error;
      form.appendChild(errorDiv);
    });
  }

  static setLoading(form, loading = true) {
    const submitBtn = form.querySelector('button[type="submit"]');
    const inputs = form.querySelectorAll("input, select, textarea");

    if (loading) {
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML =
          '<span class="spinner-border spinner-border-sm me-2"></span>جاري المعالجة...';
      }
      inputs.forEach((input) => (input.disabled = true));
    } else {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML =
          submitBtn.getAttribute("data-original-text") || "حفظ";
      }
      inputs.forEach((input) => (input.disabled = false));
    }
  }
}

// فئة إدارة الجداول
class TableManager {
  constructor(tableId, options = {}) {
    this.table = document.getElementById(tableId);
    this.options = {
      searchable: true,
      sortable: true,
      paginated: true,
      pageSize: 10,
      ...options,
    };

    if (this.table) {
      this.init();
    }
  }

  init() {
    if (this.options.searchable) {
      this.addSearchFunctionality();
    }

    if (this.options.sortable) {
      this.addSortFunctionality();
    }

    if (this.options.paginated) {
      this.addPagination();
    }
  }

  addSearchFunctionality() {
    const searchInput = document.getElementById(`${this.table.id}-search`);
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        this.search(e.target.value);
      });
    }
  }

  search(query) {
    const rows = this.table.querySelectorAll("tbody tr");
    const lowercaseQuery = query.toLowerCase();

    rows.forEach((row) => {
      const text = row.textContent.toLowerCase();
      const shouldShow = text.includes(lowercaseQuery);
      row.style.display = shouldShow ? "" : "none";
    });
  }

  addSortFunctionality() {
    const headers = this.table.querySelectorAll("thead th[data-sortable]");

    headers.forEach((header) => {
      header.style.cursor = "pointer";
      header.innerHTML += ' <i class="fas fa-sort text-muted"></i>';

      header.addEventListener("click", () => {
        this.sort(header);
      });
    });
  }

  sort(header) {
    const columnIndex = Array.from(header.parentNode.children).indexOf(header);
    const tbody = this.table.querySelector("tbody");
    const rows = Array.from(tbody.querySelectorAll("tr"));

    const currentDirection =
      header.getAttribute("data-sort-direction") || "asc";
    const newDirection = currentDirection === "asc" ? "desc" : "asc";

    // تحديث أيقونات التصنيف
    this.table.querySelectorAll("thead th i").forEach((icon) => {
      icon.className = "fas fa-sort text-muted";
    });

    const icon = header.querySelector("i");
    icon.className = `fas fa-sort-${
      newDirection === "asc" ? "up" : "down"
    } text-primary`;

    header.setAttribute("data-sort-direction", newDirection);

    // تصنيف الصفوف
    rows.sort((a, b) => {
      const aValue = a.children[columnIndex].textContent.trim();
      const bValue = b.children[columnIndex].textContent.trim();

      let result = 0;
      if (!isNaN(aValue) && !isNaN(bValue)) {
        result = parseFloat(aValue) - parseFloat(bValue);
      } else {
        result = aValue.localeCompare(bValue, "ar");
      }

      return newDirection === "asc" ? result : -result;
    });

    // إعادة ترتيب الصفوف
    rows.forEach((row) => tbody.appendChild(row));
  }

  addPagination() {
    // TODO: إضافة وظيفة التصفح إذا لزم الأمر
  }
}

// فئة إدارة المودالز
class ModalManager {
  static show(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      const bsModal = new bootstrap.Modal(modal);
      bsModal.show();
      return bsModal;
    }
  }

  static hide(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      const bsModal = bootstrap.Modal.getInstance(modal);
      if (bsModal) {
        bsModal.hide();
      }
    }
  }

  static confirm(title, message, onConfirm) {
    const modalHtml = `
            <div class="modal fade" id="confirmModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">إلغاء</button>
                            <button type="button" class="btn btn-primary" id="confirmBtn">تأكيد</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

    // إزالة مودال سابق إن وجد
    const existingModal = document.getElementById("confirmModal");
    if (existingModal) {
      existingModal.remove();
    }

    // إضافة المودال الجديد
    document.body.insertAdjacentHTML("beforeend", modalHtml);

    const modal = document.getElementById("confirmModal");
    const confirmBtn = document.getElementById("confirmBtn");

    confirmBtn.addEventListener("click", () => {
      onConfirm();
      bootstrap.Modal.getInstance(modal).hide();
    });

    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();

    // إزالة المودال بعد الإخفاء
    modal.addEventListener("hidden.bs.modal", () => {
      modal.remove();
    });
  }
}

// فئة إدارة البيانات المباشرة
class RealTimeManager {
  constructor() {
    this.intervals = {};
  }

  startPolling(name, callback, interval = 5000) {
    this.stopPolling(name);

    const poll = () => {
      callback().catch((error) => {
        console.error(`Polling error for ${name}:`, error);
      });
    };

    // تشغيل فوري
    poll();

    // تشغيل دوري
    this.intervals[name] = setInterval(poll, interval);
  }

  stopPolling(name) {
    if (this.intervals[name]) {
      clearInterval(this.intervals[name]);
      delete this.intervals[name];
    }
  }

  stopAllPolling() {
    Object.keys(this.intervals).forEach((name) => {
      this.stopPolling(name);
    });
  }
}

// إنشاء مدير البيانات المباشرة
const realTime = new RealTimeManager();

// وظائف مساعدة عامة
const Utils = {
  formatDate: (dateString) => {
    if (!dateString) return "-";
    const date = new Date(dateString);
    return date.toLocaleDateString("ar-IQ", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  },

  formatFileSize: (bytes) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  },

  formatDuration: (seconds) => {
    if (seconds < 1) return Math.round(seconds * 1000) + "ms";
    if (seconds < 60) return seconds.toFixed(1) + "s";
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  },

  formatNumber: (num) => {
    return new Intl.NumberFormat("ar-IQ").format(num);
  },

  copyToClipboard: async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      notifications.success("تم النسخ إلى الحافظة");
    } catch (error) {
      console.error("Failed to copy to clipboard:", error);
      notifications.error("فشل في النسخ إلى الحافظة");
    }
  },

  downloadFile: (data, filename, type = "application/json") => {
    const blob = new Blob([data], { type });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },

  debounce: (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  throttle: (func, limit) => {
    let inThrottle;
    return function () {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => (inThrottle = false), limit);
      }
    };
  },
};

// تهيئة التطبيق عند تحميل الصفحة
document.addEventListener("DOMContentLoaded", function () {
  console.log("TRUD - HelloCallers Proxy loaded");

  // تهيئة التلميحات
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // تهيئة الجداول التفاعلية
  document.querySelectorAll("table[data-table-enhanced]").forEach((table) => {
    new TableManager(table.id);
  });

  // تعيين النص الأصلي للأزرار
  document.querySelectorAll('button[type="submit"]').forEach((btn) => {
    btn.setAttribute("data-original-text", btn.textContent);
  });

  // إضافة مستمعين للنماذج
  document.querySelectorAll("form[data-ajax-form]").forEach((form) => {
    form.addEventListener("submit", handleAjaxForm);
  });

  // تشغيل التحديثات المباشرة إذا كانت الصفحة تتطلب ذلك
  if (document.body.hasAttribute("data-realtime")) {
    startRealTimeUpdates();
  }
});

// معالج النماذج Ajax
async function handleAjaxForm(event) {
  event.preventDefault();

  const form = event.target;
  const action = form.action || window.location.pathname;
  const method = form.method || "POST";

  FormManager.setLoading(form, true);

  try {
    const formData = FormManager.serialize(form);

    let response;
    if (method.toLowerCase() === "post") {
      response = await api.post(action, formData);
    } else if (method.toLowerCase() === "put") {
      response = await api.put(action, formData);
    } else {
      response = await api.get(action);
    }

    notifications.success("تم الحفظ بنجاح");

    // إعادة تحميل الصفحة أو إغلاق المودال حسب الحاجة
    if (form.hasAttribute("data-reload-on-success")) {
      setTimeout(() => window.location.reload(), 1000);
    }

    if (form.hasAttribute("data-close-modal-on-success")) {
      const modalId = form.getAttribute("data-close-modal-on-success");
      ModalManager.hide(modalId);
    }
  } catch (error) {
    console.error("Form submission error:", error);
    notifications.error("حدث خطأ أثناء الحفظ: " + error.message);
  } finally {
    FormManager.setLoading(form, false);
  }
}

// تشغيل التحديثات المباشرة
function startRealTimeUpdates() {
  const page = document.body.getAttribute("data-page");

  switch (page) {
    case "dashboard":
      realTime.startPolling("dashboard-stats", updateDashboardStats, 10000);
      break;
    case "sessions":
      realTime.startPolling("session-stats", updateSessionStats, 5000);
      break;
    case "accounts":
      realTime.startPolling("account-status", updateAccountStatus, 15000);
      break;
  }
}

// وظائف التحديث المباشر
async function updateDashboardStats() {
  try {
    const stats = await api.get("/sessions/stats");
    updateStatsCards(stats);
  } catch (error) {
    console.error("Failed to update dashboard stats:", error);
  }
}

async function updateSessionStats() {
  try {
    const realtimeData = await api.get("/sessions/realtime/status");
    updateRealtimeSessionData(realtimeData);
  } catch (error) {
    console.error("Failed to update session stats:", error);
  }
}

async function updateAccountStatus() {
  try {
    const accounts = await api.get("/accounts");
    updateAccountsTable(accounts);
  } catch (error) {
    console.error("Failed to update account status:", error);
  }
}

// وظائف مساعدة للتحديث
function updateStatsCards(stats) {
  // تحديث بطاقات الإحصائيات في لوحة التحكم
  Object.keys(stats).forEach((key) => {
    const element = document.getElementById(`stat-${key}`);
    if (element) {
      element.textContent = Utils.formatNumber(stats[key]);
    }
  });
}

function updateRealtimeSessionData(data) {
  // تحديث بيانات الجلسات المباشرة
  const container = document.getElementById("realtime-sessions");
  if (container && data) {
    container.innerHTML = `
            <div class="row">
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title text-primary">${Utils.formatNumber(
                              data.active_sessions || 0
                            )}</h5>
                            <p class="card-text">جلسات نشطة</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title text-success">${Utils.formatNumber(
                              data.successful_last_5min || 0
                            )}</h5>
                            <p class="card-text">نجح آخر 5 دقائق</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title text-warning">${
                              data.average_response_time
                                ? Utils.formatDuration(
                                    data.average_response_time
                                  )
                                : "-"
                            }</h5>
                            <p class="card-text">متوسط وقت الاستجابة</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h5 class="card-title text-info">${
                              data.success_rate
                                ? data.success_rate.toFixed(1)
                                : "0"
                            }%</h5>
                            <p class="card-text">معدل النجاح</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
  }
}

function updateAccountsTable(accounts) {
  // تحديث جدول الحسابات
  const tbody = document.querySelector("#accounts-table tbody");
  if (tbody && accounts) {
    tbody.innerHTML = accounts
      .map(
        (account) => `
            <tr>
                <td>${account.name || "غير محدد"}</td>
                <td>
                    <span class="badge bg-${
                      account.is_active ? "success" : "secondary"
                    }">
                        ${account.is_active ? "نشط" : "غير نشط"}
                    </span>
                </td>
                <td>
                    <span class="badge bg-${
                      account.is_banned ? "danger" : "success"
                    }">
                        ${account.is_banned ? "محظور" : "عادي"}
                    </span>
                </td>
                <td>${account.requests_today || 0}</td>
                <td>${
                  account.success_rate ? account.success_rate.toFixed(1) : "0"
                }%</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="editAccount(${
                      account.id
                    })">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteAccount(${
                      account.id
                    })">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `
      )
      .join("");
  }
}

// وظائف خاصة بصفحات محددة

// صفحة البحث
window.searchPhone = async function (phone) {
  if (!phone || phone.trim() === "") {
    notifications.warning("يرجى إدخال رقم الهاتف");
    return;
  }

  const searchBtn = document.getElementById("search-btn");
  const resultsContainer = document.getElementById("search-results");

  if (searchBtn) {
    searchBtn.disabled = true;
    searchBtn.innerHTML =
      '<span class="spinner-border spinner-border-sm me-2"></span>جاري البحث...';
  }

  try {
    const result = await api.post("/search/phone", { phone_number: phone });

    if (resultsContainer) {
      if (result.success) {
        resultsContainer.innerHTML = `
                    <div class="alert alert-success">
                        <h5>تم العثور على النتائج</h5>
                        <div class="mt-3">
                            <strong>الرقم:</strong> ${
                              result.data.phone_number || phone
                            }<br>
                            <strong>الاسم:</strong> ${
                              result.data.name || "غير متوفر"
                            }<br>
                            <strong>المشغل:</strong> ${
                              result.data.carrier || "غير متوفر"
                            }<br>
                            <strong>البلد:</strong> ${
                              result.data.country || "غير متوفر"
                            }<br>
                            <strong>نوع الرقم:</strong> ${
                              result.data.is_spam ? "مزعج" : "عادي"
                            }
                        </div>
                    </div>
                `;
      } else {
        resultsContainer.innerHTML = `
                    <div class="alert alert-warning">
                        <h5>لم يتم العثور على نتائج</h5>
                        <p>${
                          result.error || "الرقم غير موجود في قاعدة البيانات"
                        }</p>
                    </div>
                `;
      }
    }

    notifications.success("تم البحث بنجاح");
  } catch (error) {
    console.error("Search error:", error);

    if (resultsContainer) {
      resultsContainer.innerHTML = `
                <div class="alert alert-danger">
                    <h5>حدث خطأ أثناء البحث</h5>
                    <p>${error.message}</p>
                </div>
            `;
    }

    notifications.error("فشل في البحث: " + error.message);
  } finally {
    if (searchBtn) {
      searchBtn.disabled = false;
      searchBtn.innerHTML = '<i class="fas fa-search me-2"></i>بحث';
    }
  }
};

// البحث المجمع
window.bulkSearch = async function () {
  const textarea = document.getElementById("bulk-phone-numbers");
  const resultsContainer = document.getElementById("bulk-results");
  const searchBtn = document.getElementById("bulk-search-btn");

  if (!textarea || textarea.value.trim() === "") {
    notifications.warning("يرجى إدخال أرقام الهواتف");
    return;
  }

  const phoneNumbers = textarea.value
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line !== "");

  if (phoneNumbers.length === 0) {
    notifications.warning("لم يتم العثور على أرقام صالحة");
    return;
  }

  if (phoneNumbers.length > 100) {
    notifications.warning("يمكن البحث عن 100 رقم كحد أقصى في المرة الواحدة");
    return;
  }

  if (searchBtn) {
    searchBtn.disabled = true;
    searchBtn.innerHTML =
      '<span class="spinner-border spinner-border-sm me-2"></span>جاري البحث...';
  }

  try {
    const result = await api.post("/search/bulk", {
      phone_numbers: phoneNumbers,
      max_concurrent: 5,
      delay_between_requests: 1.0,
    });

    if (resultsContainer) {
      let html = `
                <div class="alert alert-info">
                    <h5>نتائج البحث المجمع</h5>
                    <div class="row mt-3">
                        <div class="col-md-3">
                            <strong>إجمالي الأرقام:</strong> ${
                              result.total_searched
                            }
                        </div>
                        <div class="col-md-3">
                            <strong>نجح:</strong> <span class="text-success">${
                              result.successful_results
                            }</span>
                        </div>
                        <div class="col-md-3">
                            <strong>فشل:</strong> <span class="text-danger">${
                              result.failed_searches
                            }</span>
                        </div>
                        <div class="col-md-3">
                            <strong>معدل النجاح:</strong> ${(
                              (result.successful_results /
                                result.total_searched) *
                              100
                            ).toFixed(1)}%
                        </div>
                    </div>
                </div>
                
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>الرقم</th>
                                <th>الحالة</th>
                                <th>الاسم</th>
                                <th>المشغل</th>
                                <th>وقت الاستجابة</th>
                                <th>النوع</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

      result.results.forEach((item) => {
        const statusBadge = item.success
          ? '<span class="badge bg-success">نجح</span>'
          : '<span class="badge bg-danger">فشل</span>';

        const spamBadge =
          item.data && item.data.is_spam
            ? '<span class="badge bg-warning">مزعج</span>'
            : '<span class="badge bg-secondary">عادي</span>';

        html += `
                    <tr>
                        <td><code>${item.phone_number}</code></td>
                        <td>${statusBadge}</td>
                        <td>${item.data ? item.data.name || "-" : "-"}</td>
                        <td>${item.data ? item.data.carrier || "-" : "-"}</td>
                        <td>${Utils.formatDuration(
                          item.response_time || 0
                        )}</td>
                        <td>${item.success ? spamBadge : "-"}</td>
                    </tr>
                `;
      });

      html += `
                        </tbody>
                    </table>
                </div>
            `;

      resultsContainer.innerHTML = html;
    }

    notifications.success(`تم البحث عن ${result.total_searched} رقم بنجاح`);
  } catch (error) {
    console.error("Bulk search error:", error);

    if (resultsContainer) {
      resultsContainer.innerHTML = `
                <div class="alert alert-danger">
                    <h5>حدث خطأ أثناء البحث المجمع</h5>
                    <p>${error.message}</p>
                </div>
            `;
    }

    notifications.error("فشل في البحث المجمع: " + error.message);
  } finally {
    if (searchBtn) {
      searchBtn.disabled = false;
      searchBtn.innerHTML = '<i class="fas fa-search me-2"></i>بحث مجمع';
    }
  }
};

// إدارة الحسابات
window.addAccount = function () {
  ModalManager.show("addAccountModal");
};

window.editAccount = async function (accountId) {
  try {
    const account = await api.get(`/accounts/${accountId}`);

    // ملء نموذج التعديل
    document.getElementById("edit-account-id").value = account.id;
    document.getElementById("edit-account-name").value = account.name || "";
    document.getElementById("edit-account-token").value = account.token || "";
    document.getElementById("edit-account-active").checked = account.is_active;

    ModalManager.show("editAccountModal");
  } catch (error) {
    notifications.error("فشل في تحميل بيانات الحساب: " + error.message);
  }
};

window.deleteAccount = function (accountId) {
  ModalManager.confirm(
    "تأكيد الحذف",
    "هل أنت متأكد من حذف هذا الحساب؟ لا يمكن التراجع عن هذا الإجراء.",
    async () => {
      try {
        await api.delete(`/accounts/${accountId}`);
        notifications.success("تم حذف الحساب بنجاح");
        setTimeout(() => window.location.reload(), 1000);
      } catch (error) {
        notifications.error("فشل في حذف الحساب: " + error.message);
      }
    }
  );
};

// إدارة البروكسيات
window.addProxy = function () {
  ModalManager.show("addProxyModal");
};

window.editProxy = async function (proxyId) {
  try {
    const proxy = await api.get(`/proxies/${proxyId}`);

    // ملء نموذج التعديل
    document.getElementById("edit-proxy-id").value = proxy.id;
    document.getElementById("edit-proxy-host").value = proxy.host || "";
    document.getElementById("edit-proxy-port").value = proxy.port || "";
    document.getElementById("edit-proxy-username").value = proxy.username || "";
    document.getElementById("edit-proxy-password").value = proxy.password || "";
    document.getElementById("edit-proxy-active").checked = proxy.is_active;

    ModalManager.show("editProxyModal");
  } catch (error) {
    notifications.error("فشل في تحميل بيانات البروكسي: " + error.message);
  }
};

window.deleteProxy = function (proxyId) {
  ModalManager.confirm(
    "تأكيد الحذف",
    "هل أنت متأكد من حذف هذا البروكسي؟",
    async () => {
      try {
        await api.delete(`/proxies/${proxyId}`);
        notifications.success("تم حذف البروكسي بنجاح");
        setTimeout(() => window.location.reload(), 1000);
      } catch (error) {
        notifications.error("فشل في حذف البروكسي: " + error.message);
      }
    }
  );
};

window.testProxy = async function (proxyId) {
  try {
    const result = await api.post(`/proxies/${proxyId}/test`);

    if (result.working) {
      notifications.success("البروكسي يعمل بشكل طبيعي");
    } else {
      notifications.warning(
        "البروكسي لا يعمل: " + (result.error || "خطأ غير معروف")
      );
    }
  } catch (error) {
    notifications.error("فشل في اختبار البروكسي: " + error.message);
  }
};

// تصدير البيانات
window.exportData = async function (type = "json") {
  try {
    const format = type === "csv" ? "csv" : "json";
    const days = document.getElementById("export-days")?.value || 7;

    const response = await fetch(
      `${API_CONFIG.baseURL}/sessions/export?format=${format}&days=${days}`,
      {
        headers: {
          Authorization: `Bearer ${API_CONFIG.apiKey}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const contentType = response.headers.get("content-type");

    if (format === "csv" || contentType.includes("text/csv")) {
      const csvData = await response.text();
      Utils.downloadFile(
        csvData,
        `sessions_export_${new Date().toISOString().split("T")[0]}.csv`,
        "text/csv"
      );
    } else {
      const jsonData = await response.json();
      const jsonString = JSON.stringify(jsonData, null, 2);
      Utils.downloadFile(
        jsonString,
        `sessions_export_${new Date().toISOString().split("T")[0]}.json`,
        "application/json"
      );
    }

    notifications.success("تم تصدير البيانات بنجاح");
  } catch (error) {
    console.error("Export error:", error);
    notifications.error("فشل في تصدير البيانات: " + error.message);
  }
};

// تنظيف البيانات القديمة
window.cleanOldData = function () {
  ModalManager.confirm(
    "تنظيف البيانات القديمة",
    "هل أنت متأكد من حذف البيانات الأقدم من 30 يوماً؟ لا يمكن التراجع عن هذا الإجراء.",
    async () => {
      try {
        const result = await api.delete("/sessions/cleanup?days=30");
        notifications.success(`تم حذف ${result.deleted_count} جلسة قديمة`);
        setTimeout(() => window.location.reload(), 2000);
      } catch (error) {
        notifications.error("فشل في تنظيف البيانات: " + error.message);
      }
    }
  );
};

// وظائف التحكم في النظام
window.restartSystem = function () {
  ModalManager.confirm(
    "إعادة تشغيل النظام",
    "هل أنت متأكد من إعادة تشغيل النظام؟ سيتم قطع جميع الاتصالات الحالية.",
    async () => {
      try {
        await api.post("/system/restart");
        notifications.info("تم إرسال أمر إعادة التشغيل");
        setTimeout(() => window.location.reload(), 5000);
      } catch (error) {
        notifications.error("فشل في إعادة تشغيل النظام: " + error.message);
      }
    }
  );
};

// مساعدات التنقل
window.goToPage = function (page) {
  window.location.href = page;
};

window.refreshPage = function () {
  window.location.reload();
};

// تنظيف الموارد عند مغادرة الصفحة
window.addEventListener("beforeunload", function () {
  realTime.stopAllPolling();
});

// إضافة أحداث لوحة المفاتيح
document.addEventListener("keydown", function (event) {
  // Ctrl/Cmd + Enter للإرسال السريع في النماذج
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    const activeForm = document.activeElement.closest("form");
    if (activeForm) {
      activeForm.dispatchEvent(new Event("submit"));
    }
  }

  // ESC لإغلاق المودالز
  if (event.key === "Escape") {
    const openModals = document.querySelectorAll(".modal.show");
    openModals.forEach((modal) => {
      const bsModal = bootstrap.Modal.getInstance(modal);
      if (bsModal) {
        bsModal.hide();
      }
    });
  }
});

// تصدير الكائنات للاستخدام العام
window.TRUD = {
  api,
  notifications,
  FormManager,
  TableManager,
  ModalManager,
  realTime,
  Utils,
};

console.log("TRUD JavaScript loaded successfully");
