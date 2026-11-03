/**
 * Anti-Money Laundering (AML) Hybrid Platform Frontend Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  loadLiveStream();
  loadCases();
  loadMetrics();
  loadMLOps();
  loadTypologies();
  loadAuditChain();

  // Periodic polling for live telemetry
  setInterval(loadLiveStream, 5000);
});

// Toast Helper
function showToast(message, isError = false) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.innerText = message;
  toast.style.borderColor = isError ? 'var(--accent-crimson)' : 'var(--accent-indigo)';
  toast.style.display = 'block';
  setTimeout(() => {
    toast.style.display = 'none';
  }, 3500);
}

// Tab Switching
function initTabs() {
  const tabs = document.querySelectorAll('.nav-tab');
  const panes = document.querySelectorAll('.tab-pane');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      panes.forEach(p => p.classList.remove('active'));

      tab.classList.add('active');
      const targetId = tab.getAttribute('data-tab');
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add('active');
    });
  });
}

// 1. Live Stream Loader
async function loadLiveStream() {
  try {
    const res = await fetch('/api/transactions/stream?limit=15');
    if (!res.ok) return;
    const stream = await res.json();

    const tbody = document.getElementById('stream-tbody');
    if (!tbody) return;

    if (stream.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No transactions in stream. Click "Inject Seed Stream" to begin.</td></tr>';
      return;
    }

    tbody.innerHTML = stream.map(txn => {
      let badgeClass = 'badge-low';
      if (txn.status === 'HOLD' || txn.tier1_status === 'HOLD') badgeClass = 'badge-critical';
      else if (txn.status === 'TRIAGING' || txn.tier2_score >= 0.35) badgeClass = 'badge-intermediate';
      else if (txn.status === 'AUTO_CLEARED' || txn.status === 'PASSED') badgeClass = 'badge-low';

      return `
        <tr>
          <td><span class="hash-pill">${txn.transaction_id}</span></td>
          <td>${txn.timestamp.split('T')[1].split('.')[0]}</td>
          <td><strong>$${Number(txn.amount).toLocaleString('en-US', {minimumFractionDigits: 2})}</strong></td>
          <td>${txn.sender} &rarr; ${txn.receiver}</td>
          <td><span class="badge ${badgeClass}">${txn.tier1_status} (${txn.tier1_latency_ms}ms)</span></td>
          <td><strong>${txn.tier2_score.toFixed(3)}</strong></td>
          <td><span class="badge ${badgeClass}">${txn.status}</span></td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error('Failed loading stream', err);
  }
}

// Inject Seed Stream Action
async function injectSeedStream() {
  try {
    showToast('Injecting multi-typology seed transactions...');
    const res = await fetch('/api/transactions/seed-populate');
    const data = await res.json();
    showToast(data.message);
    loadLiveStream();
    loadCases();
    loadMetrics();
    loadAuditChain();
  } catch (err) {
    showToast('Failed injecting stream', true);
  }
}

// 2. Case Management & HITL
async function loadCases() {
  try {
    const res = await fetch('/api/cases');
    if (!res.ok) return;
    const cases = await res.json();

    const tbody = document.getElementById('cases-tbody');
    if (!tbody) return;

    if (cases.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No cases pending review. Run simulation or inject seed data.</td></tr>';
      return;
    }

    tbody.innerHTML = cases.map(c => {
      let badgeClass = 'badge-intermediate';
      if (c.status === 'SAR_APPROVED') badgeClass = 'badge-approved';
      if (c.status === 'SAR_OVERRIDDEN') badgeClass = 'badge-amber';
      if (c.status === 'AUTO_CLEARED') badgeClass = 'badge-low';
      if (c.status === 'HOLD' || c.status === 'ESCALATED_HUMAN') badgeClass = 'badge-critical';

      return `
        <tr>
          <td><span class="hash-pill">${c.case_id}</span></td>
          <td>${c.alert.transaction.sender.name}</td>
          <td><strong>$${Number(c.alert.transaction.amount).toLocaleString('en-US', {minimumFractionDigits: 2})}</strong></td>
          <td><span class="badge badge-indigo">${c.alert.ml_scoring.inferred_typology}</span></td>
          <td><strong>${c.alert.ml_scoring.s_final.toFixed(3)}</strong></td>
          <td><span class="badge ${badgeClass}">${c.status}</span></td>
          <td>
            <button class="btn btn-secondary" style="padding:0.25rem 0.6rem; font-size:0.75rem;" onclick="openCaseModal('${c.case_id}')">
              Review Dossier
            </button>
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error('Failed loading cases', err);
  }
}

// Open Case Dossier Modal
async function openCaseModal(caseId) {
  try {
    const res = await fetch(`/api/cases/${caseId}`);
    if (!res.ok) return;
    const c = await res.json();

    const modal = document.getElementById('case-modal');
    const content = document.getElementById('case-modal-content');
    if (!modal || !content) return;

    const sar = c.draft_sar || {};
    const txn = c.alert.transaction;
    const ml = c.alert.ml_scoring;
    const dossier = c.dossier;

    content.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem;">
        <div>
          <h2>Adjudication Dossier: ${c.case_id}</h2>
          <p style="color:var(--text-secondary); font-size:0.85rem;">Subject: ${txn.sender.name} | Account: ${txn.sender.account_id} | Status: <span class="badge badge-intermediate">${c.status}</span></p>
        </div>
        <button class="btn btn-secondary" onclick="closeCaseModal()">Close</button>
      </div>

      <div class="grid-3" style="margin-bottom:1.5rem;">
        <div class="stat-card">
          <div class="stat-label">Flagged Amount</div>
          <div class="stat-value">$${Number(txn.amount).toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
          <div class="stat-sub">${txn.channel} via ${txn.payment_rail}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Composite Risk Score</div>
          <div class="stat-value" style="color:var(--accent-crimson);">${ml.s_final.toFixed(3)}</div>
          <div class="stat-sub">Sup: ${ml.s_supervised.toFixed(2)} | AE: ${ml.s_unsupervised.toFixed(2)} | GNN: ${ml.s_graph.toFixed(2)}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Critic Groundedness</div>
          <div class="stat-value" style="color:var(--accent-emerald);">${(dossier.groundedness_score * 100).toFixed(1)}%</div>
          <div class="stat-sub">Zero-Hallucination Guardrail Passed</div>
        </div>
      </div>

      <div class="panel" style="background:rgba(0,0,0,0.3);">
        <h3>Compliance Counterfactual (SR 11-7)</h3>
        <p style="font-size:0.85rem; color:var(--accent-cyan); margin-top:0.5rem; font-family:'JetBrains Mono', monospace;">
          ${ml.counterfactual_explanation || 'No counterfactual available.'}
        </p>
      </div>

      <div class="panel" style="background:rgba(0,0,0,0.3);">
        <h3>Multi-Agent Evidence Synthesis</h3>
        <div style="font-size:0.8rem; margin-top:0.5rem; display:flex; flex-direction:column; gap:0.5rem;">
          <div><strong>Entity Resolution:</strong> ${dossier.entity_findings?.summary || 'N/A'}</div>
          <div><strong>Transaction Forensics:</strong> ${dossier.forensic_findings?.summary || 'N/A'}</div>
          <div><strong>External OSINT & Adverse Media:</strong> ${dossier.osint_findings?.summary || 'N/A'}</div>
        </div>
      </div>

      <div class="panel" style="background:rgba(0,0,0,0.3);">
        <h3>FinCEN Draft SAR Narrative</h3>
        <textarea id="sar-narrative-editor" style="width:100%; height:160px; background:rgba(14,21,36,0.9); color:#ffffff; border:1px solid var(--border-subtle); border-radius:var(--radius-sm); padding:0.75rem; font-family:'JetBrains Mono', monospace; font-size:0.78rem; margin-top:0.5rem;">${sar.narrative || 'No narrative generated.'}</textarea>
      </div>

      <div style="display:flex; justify-content:flex-end; gap:1rem; margin-top:1.5rem; border-top:1px solid var(--border-subtle); padding-top:1rem;">
        <button class="btn btn-secondary" onclick="overrideCase('${c.case_id}')">Override / Clear (Audit Code)</button>
        <button class="btn btn-primary" onclick="approveCase('${c.case_id}')">Approve SAR Filing</button>
        <button class="btn btn-success" onclick="submitCaseToFinCEN('${c.case_id}')">Submit to FinCEN Gateway</button>
      </div>
    `;

    modal.classList.add('active');
  } catch (err) {
    showToast('Failed opening case dossier', true);
  }
}

function closeCaseModal() {
  const modal = document.getElementById('case-modal');
  if (modal) modal.classList.remove('active');
}

// Approve Case
async function approveCase(caseId) {
  try {
    const editor = document.getElementById('sar-narrative-editor');
    const narrative = editor ? editor.value : null;

    const res = await fetch(`/api/cases/${caseId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        analyst_id: 'AML_OFFICER_CHENG_04',
        notes: 'Approved based on GNN peeling chain analysis and verified BVI corporate shell tree.',
        edited_narrative: narrative,
      }),
    });
    if (res.ok) {
      showToast(`Case ${caseId} approved for filing!`);
      closeCaseModal();
      loadCases();
      loadAuditChain();
    }
  } catch (err) {
    showToast('Failed approving case', true);
  }
}

// Override Case
async function overrideCase(caseId) {
  const reasonCode = prompt('Enter Mandatory Override Reason Code (e.g. FALSE_POSITIVE_KNOWN_BUSINESS, LEGITIMATE_COMMODITY_HEDGE, INSUFFICIENT_EVIDENCE):', 'FALSE_POSITIVE_KNOWN_BUSINESS');
  if (!reasonCode) return;

  const notes = prompt('Enter Investigator Audit Justification Notes:', 'Customer verified as bona fide regional agricultural distributor with high seasonal turnover.');
  if (!notes) return;

  try {
    const res = await fetch(`/api/cases/${caseId}/override`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        analyst_id: 'AML_OFFICER_CHENG_04',
        override_reason_code: reasonCode,
        justification_notes: notes,
      }),
    });
    if (res.ok) {
      showToast(`Case ${caseId} overridden with code ${reasonCode}.`);
      closeCaseModal();
      loadCases();
      loadAuditChain();
    }
  } catch (err) {
    showToast('Failed overriding case', true);
  }
}

// Submit to FinCEN Gateway
async function submitCaseToFinCEN(caseId) {
  try {
    const res = await fetch(`/api/cases/${caseId}/submit-sar`, { method: 'POST' });
    const data = await res.json();
    if (res.ok) {
      showToast(`SAR successfully transmitted! Receipt: ${data.receipt.filing_receipt_id}`);
      closeCaseModal();
      loadCases();
      loadAuditChain();
    } else {
      showToast(data.detail || 'Filing submission failed', true);
    }
  } catch (err) {
    showToast('Regulatory gateway submission error', true);
  }
}

// 3. 5-Tier Metrics Observatory Loader
async function loadMetrics() {
  try {
    const res = await fetch('/api/metrics/all');
    if (!res.ok) return;
    const data = await res.json();

    const b = data.business_metrics;
    const s = data.system_metrics;
    const r = data.rag_metrics;
    const a = data.agentic_metrics;
    const m = data.ml_metrics;

    // Business
    setVal('biz-conv-rate', `${(b.alert_to_sar_conversion_rate * 100).toFixed(1)}%`);
    setVal('biz-mtti', `${b.mtti_metrics.current_mtti_minutes} min`);
    setVal('biz-cost', `$${b.cost_per_resolved_alert_usd}`);
    setVal('biz-savings', `$${b.labor_savings.net_labor_savings_usd.toLocaleString()}`);

    // System
    setVal('sys-t1-p99', `${s.tier1_latency_ms.p99} ms`);
    setVal('sys-t2-p99', `${s.tier2_latency_ms.p99} ms`);
    setVal('sys-tps', `${s.throughput_tps.toLocaleString()} TPS`);
    setVal('sys-transit-sat', `${s.cloud_interconnect_saturation_pct}%`);

    // RAG Triad
    setVal('rag-faithfulness', `${(r.faithfulness_score * 100).toFixed(1)}%`);
    setVal('rag-relevance', `${(r.context_relevance_score * 100).toFixed(1)}%`);
    setVal('rag-completeness', `${(r.answer_completeness_score * 100).toFixed(1)}%`);
    setVal('rag-index', `${(r.rag_triad_index * 100).toFixed(1)}%`);

    // Agentic
    setVal('agent-plan-rate', `${(a.plan_completion_rate * 100).toFixed(1)}%`);
    setVal('agent-clearance-acc', `${(a.autonomous_clearance_accuracy * 100).toFixed(1)}%`);
    setVal('agent-critic-reject', `${(a.critic_rejection_rate * 100).toFixed(1)}%`);
    setVal('agent-tools-avg', `${a.avg_tools_per_investigation}`);

    // ML Metrics
    setVal('ml-prauc', `${m.pr_auc.toFixed(3)}`);
    setVal('ml-prec-k', `${(m.precision_at_k * 100).toFixed(1)}%`);
    setVal('ml-ece', `${m.expected_calibration_error.toFixed(4)}`);
    setVal('ml-brier', `${m.brier_score.toFixed(4)}`);
  } catch (err) {
    console.error('Failed loading metrics', err);
  }
}

function setVal(id, text) {
  const el = document.getElementById(id);
  if (el) el.innerText = text;
}

// 4. MLOps Drift & Shadow Loader
async function loadMLOps() {
  try {
    const driftRes = await fetch('/api/mlops/drift');
    const shadowRes = await fetch('/api/mlops/shadow');
    const modelsRes = await fetch('/api/mlops/models');

    if (driftRes.ok) {
      const drift = await driftRes.json();
      setVal('drift-action', drift.recommended_action);
      setVal('drift-ph', `${drift.page_hinkley_metric.toFixed(3)}`);

      const psiList = document.getElementById('psi-list');
      if (psiList) {
        psiList.innerHTML = Object.entries(drift.feature_psi).map(([feat, val]) => `
          <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem; font-size:0.8rem;">
            <span>${feat}</span>
            <span class="badge ${val >= 0.25 ? 'badge-critical' : (val >= 0.10 ? 'badge-amber' : 'badge-low')}">PSI: ${val.toFixed(4)}</span>
          </div>
        `).join('');
      }
    }

    if (shadowRes.ok) {
      const shadow = await shadowRes.json();
      setVal('shadow-div-rate', `${(shadow.divergence_rate * 100).toFixed(1)}%`);
    }

    if (modelsRes.ok) {
      const models = await modelsRes.json();
      const mBody = document.getElementById('models-tbody');
      if (mBody) {
        mBody.innerHTML = models.map(m => `
          <tr>
            <td><strong>${m.name}</strong></td>
            <td><span class="hash-pill">${m.version}</span></td>
            <td><span class="badge ${m.status === 'CHAMPION' ? 'badge-approved' : 'badge-amber'}">${m.status}</span></td>
            <td>${m.prauc_score.toFixed(3)}</td>
            <td>${m.f1_score.toFixed(3)}</td>
          </tr>
        `).join('');
      }
    }
  } catch (err) {
    console.error('Failed loading MLOps', err);
  }
}

// 5. Typology Catalog & 1-Click Simulation
async function loadTypologies() {
  try {
    const res = await fetch('/api/typologies/catalog');
    if (!res.ok) return;
    const catalog = await res.json();

    const container = document.getElementById('typologies-container');
    if (!container) return;

    container.innerHTML = catalog.map(t => `
      <div class="typology-card">
        <div>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
            <span class="badge badge-indigo">Typology #${t.id}</span>
            <span style="font-size:0.7rem; color:var(--text-muted); font-family:'JetBrains Mono';">${t.seed_id}</span>
          </div>
          <h3>${t.title}</h3>
          <p><strong>Pattern:</strong> ${t.adversarial_pattern}</p>
          <p style="color:var(--accent-cyan); font-size:0.75rem;"><strong>Resolution:</strong> ${t.resolution_tier} &mdash; ${t.resolution_details}</p>
        </div>
        <button class="btn btn-primary" style="margin-top:1rem; width:100%; justify-content:center;" onclick="simulateTypology(${t.id})">
          Simulate Typology #${t.id}
        </button>
      </div>
    `).join('');
  } catch (err) {
    console.error('Failed loading typologies', err);
  }
}

// Simulate Single Typology
async function simulateTypology(typologyId) {
  try {
    showToast(`Triggering Typology #${typologyId} simulation...`);
    const res = await fetch(`/api/typologies/simulate/${typologyId}`, { method: 'POST' });
    const data = await res.json();

    showToast(`Simulation for '${data.typology.title}' finished! Status: ${data.simulation_result.event.status}`);
    loadLiveStream();
    loadCases();
    loadMetrics();
    loadAuditChain();

    if (data.simulation_result.event.case_id) {
      setTimeout(() => {
        openCaseModal(data.simulation_result.event.case_id);
      }, 700);
    }
  } catch (err) {
    showToast('Failed running typology simulation', true);
  }
}

// 6. Cryptographic Audit Chain Loader
async function loadAuditChain() {
  try {
    const res = await fetch('/api/audit/chain?limit=15');
    if (!res.ok) return;
    const chain = await res.json();

    const tbody = document.getElementById('audit-tbody');
    if (!tbody) return;

    tbody.innerHTML = chain.reverse().map(b => `
      <tr>
        <td><strong>#${b.block_index}</strong></td>
        <td><span class="badge badge-indigo">${b.event_type}</span></td>
        <td><span class="hash-pill">${b.current_hash.slice(0, 16)}...</span></td>
        <td><span class="hash-pill" style="color:var(--text-muted);">${b.previous_hash.slice(0, 16)}...</span></td>
        <td>${b.actor}</td>
        <td style="font-size:0.75rem; color:var(--text-muted);">${b.timestamp.split('T')[1].split('.')[0]}</td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Failed loading audit chain', err);
  }
}

// Verify Cryptographic Hash Chain Integrity
async function verifyChainIntegrity() {
  try {
    showToast('Validating SHA-256 block chain from Genesis...');
    const res = await fetch('/api/audit/verify');
    const data = await res.json();

    if (data.is_valid) {
      alert(`WORM Cryptographic Chain Verified!\nChain Length: ${data.chain_length} blocks\nHead Hash: ${data.head_hash}\nAll hashes and forward links are 100% authentic and tamper-free.`);
      showToast('Cryptographic chain verified authentic!');
    } else {
      alert(`CHAIN TAMPERING DETECTED!\nError: ${data.error}`);
      showToast('Chain integrity check failed!', true);
    }
  } catch (err) {
    showToast('Error validating chain', true);
  }
}
