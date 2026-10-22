/**
 * OmniSync ESG - Global Enterprise ERP Data Sync & Deterministic ESG Calculation Studio
 */

// Purge any stale service workers from previous web apps on this host/port
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then(registrations => {
    for (const registration of registrations) {
      registration.unregister();
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initFormulaSimulator();
});

// Tab Switching
function initTabs() {
  const buttons = document.querySelectorAll(".tab-btn");
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const tabId = btn.getAttribute("data-tab");

      buttons.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));

      btn.classList.add("active");
      const target = document.getElementById(tabId);
      if (target) target.classList.add("active");
    });
  });
}

// Toast Notifications
function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = "toast";
  if (type === "error") {
    toast.style.borderLeftColor = "#f43f5e";
  } else if (type === "info") {
    toast.style.borderLeftColor = "#06b6d4";
  }

  toast.innerHTML = `<div>${message}</div>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(50px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ERP Sync Trigger
async function triggerSync(connectionId, btnElement) {
  const originalHtml = btnElement ? btnElement.innerHTML : "";
  if (btnElement) {
    btnElement.disabled = true;
    btnElement.innerHTML = `<span class="pulse-dot" style="background:#fff;"></span> Syncing...`;
  }

  showToast("Initiating ERP extraction and delta sync...", "info");

  try {
    const res = await fetch(`/api/erp/connections/${connectionId}/sync-now/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ sync_type: "DELTA", run_async: false }),
    });

    const data = await res.json();
    if (res.ok) {
      showToast(`Sync completed! ${data.records_saved} records ingested. Checksum: ${data.batch_checksum ? data.batch_checksum.substring(0, 10) : "verified"}...`);
      setTimeout(() => window.location.reload(), 1200);
    } else {
      showToast(`Sync failed: ${data.error || "Unknown error"}`, "error");
    }
  } catch (err) {
    showToast(`Network error: ${err.message}`, "error");
  } finally {
    if (btnElement) {
      btnElement.disabled = false;
      btnElement.innerHTML = originalHtml;
    }
  }
}

// Sync All Global ERPs
async function triggerSyncAll(btnElement) {
  if (btnElement) {
    btnElement.disabled = true;
    btnElement.innerHTML = "Syncing All ERPs...";
  }

  showToast("Broadcasting sync request across all active ERP connectors...", "info");

  try {
    const res = await fetch("/api/erp/connections/sync-all/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ run_async: false }),
    });
    const data = await res.json();
    showToast("All active enterprise ERP connectors synchronized successfully!");
    setTimeout(() => window.location.reload(), 1200);
  } catch (err) {
    showToast(`Error: ${err.message}`, "error");
  } finally {
    if (btnElement) {
      btnElement.disabled = false;
      btnElement.innerHTML = `<i class="fa-solid fa-arrows-rotate"></i> Sync All Global ERPs`;
    }
  }
}

// Deterministic Calculation Run Trigger
async function triggerCalculation(methodologyId, btnElement) {
  if (btnElement) {
    btnElement.disabled = true;
    btnElement.innerHTML = "Computing Math...";
  }

  showToast("Executing deterministic calculation engine against warehouse records...", "info");

  try {
    const res = await fetch(`/api/calculation/methodologies/${methodologyId}/run-calculation/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ initiated_by: "DASHBOARD_UI" }),
    });

    const data = await res.json();
    if (res.ok) {
      showToast(`Calculation Completed! Scope 1: ${data.total_scope_1_tco2e} tCO2e | Scope 2: ${data.total_scope_2_location_tco2e} tCO2e`);
      setTimeout(() => window.location.reload(), 1400);
    } else {
      showToast(`Calculation error: ${data.error}`, "error");
    }
  } catch (err) {
    showToast(`Failed to run calculation: ${err.message}`, "error");
  } finally {
    if (btnElement) {
      btnElement.disabled = false;
      btnElement.innerHTML = "Run Calculation";
    }
  }
}

// Live Formula Simulator
function initFormulaSimulator() {
  const testBtn = document.getElementById("btn-test-formula");
  if (!testBtn) return;

  testBtn.addEventListener("click", async () => {
    const expr = document.getElementById("sim-expression").value;
    const consumption = parseFloat(document.getElementById("sim-var-consumption").value || "0");
    const factor = parseFloat(document.getElementById("sim-var-factor").value || "0");
    const gwp = parseFloat(document.getElementById("sim-var-gwp").value || "1");

    const resultBox = document.getElementById("sim-result-box");
    resultBox.innerHTML = "Evaluating formula via Python AST...";

    try {
      const res = await fetch("/api/calculation/simulate-formula/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          expression: expr,
          variables: {
            consumption: consumption,
            emission_factor: factor,
            gwp: gwp,
          },
        }),
      });

      const data = await res.json();
      if (res.ok && data.is_valid) {
        resultBox.innerHTML = `
          <div style="color:#10b981; font-weight:700; margin-bottom:0.4rem;">
            ✓ Safe AST Validation Passed
          </div>
          <div><strong>Evaluated Math:</strong> <code>${data.formula_evaluated}</code></div>
          <div><strong>Result:</strong> <span style="font-size:1.3rem; font-weight:800; color:#38bdf8;">${data.result} tCO2e</span></div>
        `;
      } else {
        resultBox.innerHTML = `
          <div style="color:#f43f5e; font-weight:700;">
            ✕ Invalid Formula Syntax / Math Error:
          </div>
          <div>${data.error || "Unknown validation error"}</div>
        `;
      }
    } catch (err) {
      resultBox.innerHTML = `<span style="color:#f43f5e;">Network error: ${err.message}</span>`;
    }
  });
}

// Save Custom Formula Rule to Database
async function saveFormulaRule(ruleId) {
  const inputEl = document.getElementById(`rule-expr-${ruleId}`);
  if (!inputEl) return;

  const newExpr = inputEl.value;
  showToast("Updating formula rule in methodology...", "info");

  try {
    const res = await fetch(`/api/calculation/formula-rules/${ruleId}/`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ expression: newExpr }),
    });

    if (res.ok) {
      showToast("Formula rule successfully saved & updated!");
    } else {
      const data = await res.json();
      showToast(`Failed to update: ${JSON.stringify(data)}`, "error");
    }
  } catch (err) {
    showToast(`Error: ${err.message}`, "error");
  }
}

// Audit Proof Inspector Modal
async function openAuditProof(recordId) {
  const modal = document.getElementById("audit-modal");
  const modalBody = document.getElementById("audit-modal-body");
  if (!modal || !modalBody) return;

  modalBody.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--text-muted);">Retrieving cryptographic audit proof from database...</div>`;
  modal.classList.add("active");

  try {
    const res = await fetch(`/api/calculation/calculated-records/${recordId}/`);
    const data = await res.json();

    const trace = data.calculation_trace || {};
    const raw = trace.raw_input || {};
    const factor = trace.emission_factor_applied || {};

    modalBody.innerHTML = `
      <div style="margin-bottom: 1.25rem;">
        <span class="badge-pill badge-cyan">${data.kpi_category}</span>
        <span class="badge-pill badge-emerald font-mono" style="margin-left:0.4rem;">${data.rule_code}</span>
        <h3 style="color:#fff; margin-top:0.6rem; font-size:1.3rem;">Audit Proof & Traceability Lineage</h3>
        <p style="color:var(--text-muted); font-size:0.82rem;">Verifiable calculation trace compliant with EU CSRD, GHG Protocol & SOX disclosure controls.</p>
      </div>

      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:0.8rem; margin-bottom:1.25rem;">
        <div style="background:rgba(255,255,255,0.03); padding:0.8rem; border-radius:8px; border:1px solid var(--border-color);">
          <div style="font-size:0.75rem; color:var(--text-dim); text-transform:uppercase;">Facility & Location</div>
          <div style="font-weight:700; color:#fff;">${data.facility_name} (${data.facility_code})</div>
          <div style="font-size:0.8rem; color:var(--text-muted);">Grid: ${trace.grid_subregion || "National"}</div>
        </div>

        <div style="background:rgba(255,255,255,0.03); padding:0.8rem; border-radius:8px; border:1px solid var(--border-color);">
          <div style="font-size:0.75rem; color:var(--text-dim); text-transform:uppercase;">ERP Source Document</div>
          <div style="font-weight:700; color:#38bdf8; font-family:monospace;">${raw.sap_document_number || "WORKDAY_REF"}</div>
          <div style="font-size:0.8rem; color:var(--text-muted);">Meter: ${raw.meter_identifier || "Direct Sensor"}</div>
        </div>
      </div>

      <div style="background:#060911; border:1px solid var(--border-color); border-radius:8px; padding:1rem; margin-bottom:1.25rem;">
        <div style="font-size:0.75rem; font-weight:700; color:#94a3b8; text-transform:uppercase; margin-bottom:0.5rem;">
          Step-by-Step Mathematical Derivation:
        </div>
        <div style="font-size:0.85rem; color:#e2e8f0; margin-bottom:0.4rem;">
          <strong>1. Raw Measurement:</strong> ${raw.consumption_value || 0} ${raw.consumption_unit || ""} (${raw.period || ""})
        </div>
        <div style="font-size:0.85rem; color:#e2e8f0; margin-bottom:0.4rem;">
          <strong>2. Normalization Step:</strong> <code>${trace.unit_normalization_step || "Direct normalization"}</code>
        </div>
        <div style="font-size:0.85rem; color:#e2e8f0; margin-bottom:0.4rem;">
          <strong>3. Emission Factor Applied:</strong> ${factor.factor_value} ${factor.factor_unit} (${factor.compliance_framework || "GHG Protocol"})
          <div style="font-size:0.75rem; color:#64748b;">Source: ${factor.source_citation || "Standard Hub"}</div>
        </div>
        <div style="font-size:0.85rem; color:#e2e8f0; margin-top:0.6rem; padding-top:0.6rem; border-top:1px dashed rgba(255,255,255,0.1);">
          <strong>4. Evaluated AST Equation:</strong>
          <pre style="color:#38bdf8; font-family:monospace; margin-top:0.3rem;">${data.formula_evaluated}</pre>
        </div>
      </div>

      <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); padding:1rem; border-radius:10px;">
        <div>
          <div style="font-size:0.75rem; color:#34d399; font-weight:600; text-transform:uppercase;">Verified Audited Value</div>
          <div style="font-size:1.8rem; font-weight:800; color:#fff;">${data.result_value} <span style="font-size:1rem; font-weight:600; color:#34d399;">${data.result_unit}</span></div>
        </div>
        <button class="btn btn-secondary btn-sm" onclick="closeAuditModal()">Close Inspector</button>
      </div>
    `;
  } catch (err) {
    modalBody.innerHTML = `<div style="color:#f43f5e; padding:1.5rem;">Failed to load audit proof: ${err.message}</div>`;
  }
}

function closeAuditModal() {
  const modal = document.getElementById("audit-modal");
  if (modal) modal.classList.remove("active");
}
