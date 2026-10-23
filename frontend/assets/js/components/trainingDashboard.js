/**
 * SignSpeak - Model Training & Evaluation Dashboard Component
 * Controls dataset validation, manifest preparation, model training lifecycle,
 * held-out evaluation, and deployment to live webcam inference.
 */

export class TrainingDashboardHandler {
    constructor() {
        this.currentManifestPath = null;
        this.trainingPollTimer = null;
    }

    init() {
        this.bindEvents();
        this.loadAdapters();
        this.loadManifests();
        this.loadRegisteredModels();
    }

    bindEvents() {
        // Dataset validation
        const validateBtn = document.getElementById('validateDatasetBtn');
        const createManifestBtn = document.getElementById('createManifestBtn');
        if (validateBtn) validateBtn.addEventListener('click', () => this.validateDataset());
        if (createManifestBtn) createManifestBtn.addEventListener('click', () => this.createManifest());

        // Training
        const startTrainBtn = document.getElementById('startTrainingBtn');
        const cancelTrainBtn = document.getElementById('cancelTrainingBtn');
        if (startTrainBtn) startTrainBtn.addEventListener('click', () => this.startTraining());
        if (cancelTrainBtn) cancelTrainBtn.addEventListener('click', () => this.cancelTraining());

        // Refresh models
        const refreshModelsBtn = document.getElementById('refreshModelsBtn');
        if (refreshModelsBtn) refreshModelsBtn.addEventListener('click', () => this.loadRegisteredModels());
    }

    async loadAdapters() {
        const selectEl = document.getElementById('datasetAdapterSelect');
        if (!selectEl) return;

        try {
            const res = await fetch('/api/v1/datasets/adapters');
            if (!res.ok) return;
            const adapters = await res.json();
            selectEl.innerHTML = '';
            adapters.forEach(a => {
                const opt = document.createElement('option');
                opt.value = a.name.toLowerCase();
                opt.textContent = `${a.name} (${a.annotation_type}) - ${a.license}`;
                selectEl.appendChild(opt);
            });
        } catch (err) {
            console.warn('Failed loading adapters:', err);
        }
    }

    async loadManifests() {
        const manifestSelect = document.getElementById('trainManifestSelect');
        if (!manifestSelect) return;

        try {
            const res = await fetch('/api/v1/datasets/manifests');
            if (!res.ok) return;
            const manifests = await res.json();
            manifestSelect.innerHTML = '<option value="">-- Select a Generated Manifest --</option>';
            manifests.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m.relative_path;
                opt.textContent = `${m.filename} [${m.dataset_name || 'Dataset'}] (${m.total_samples} samples, Task: ${m.task})`;
                manifestSelect.appendChild(opt);
            });
        } catch (err) {
            console.warn('Failed loading manifests:', err);
        }
    }

    async validateDataset() {
        const adapter = document.getElementById('datasetAdapterSelect')?.value;
        const path = document.getElementById('datasetPathInput')?.value.trim();
        const resultsEl = document.getElementById('datasetValidationResults');

        if (!path) {
            alert('Please specify a dataset directory path.');
            return;
        }

        if (resultsEl) {
            resultsEl.innerHTML = '<div class="loading-spinner">Validating dataset files and split integrity...</div>';
            resultsEl.classList.remove('hidden');
        }

        try {
            const res = await fetch('/api/v1/datasets/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ adapter: adapter, dataset_path: path })
            });

            const data = await res.json();
            this.renderValidationReport(data);
        } catch (err) {
            if (resultsEl) resultsEl.innerHTML = `<div class="error-badge">Validation request failed: ${err.message}</div>`;
        }
    }

    renderValidationReport(report) {
        const resultsEl = document.getElementById('datasetValidationResults');
        if (!resultsEl) return;

        const isValid = report.is_valid;
        const statusBadge = isValid ? '<span class="badge badge-success">✓ VALID DATASET</span>' : '<span class="badge badge-error">✕ VALIDATION FAILED</span>';
        const leakageWarning = report.signer_leakage_detected
            ? `<div class="alert alert-warning">⚠️ Signer Leakage Warning: ${report.signer_leakage_details}</div>`
            : '';

        const splitBadges = Object.entries(report.split_counts || {})
            .map(([split, count]) => `<span class="split-pill"><strong>${split}</strong>: ${count}</span>`)
            .join(' ');

        const warningsHtml = (report.warnings || []).map(w => `<li>⚠️ ${w}</li>`).join('');
        const errorsHtml = (report.errors || []).map(e => `<li>🚨 ${e}</li>`).join('');

        resultsEl.innerHTML = `
            <div class="report-card">
                <div class="report-header">
                    <h4>${report.dataset_name} (${report.dataset_version})</h4>
                    ${statusBadge}
                </div>
                ${leakageWarning}
                <div class="report-stats">
                    <div class="stat-box">
                        <span class="stat-num">${report.valid_count}</span>
                        <span class="stat-lbl">Valid Samples</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-num">${report.missing_files_count}</span>
                        <span class="stat-lbl">Missing Videos</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-num">${(report.signer_ids || []).length}</span>
                        <span class="stat-lbl">Unique Signers</span>
                    </div>
                </div>
                <div class="report-splits">
                    <strong>Split Counts:</strong> ${splitBadges || 'None defined'}
                </div>
                <div class="report-license">
                    <p><strong>License:</strong> ${report.license_notes || 'Not specified'}</p>
                    <p><strong>Attribution:</strong> ${report.attribution || 'Not specified'}</p>
                    <p><strong>Compatible Tasks:</strong> ${(report.compatible_tasks || []).join(', ')}</p>
                </div>
                ${warningsHtml || errorsHtml ? `<ul class="report-messages">${errorsHtml}${warningsHtml}</ul>` : ''}
            </div>
        `;
    }

    async createManifest() {
        const adapter = document.getElementById('datasetAdapterSelect')?.value;
        const path = document.getElementById('datasetPathInput')?.value.trim();
        const task = document.getElementById('trainTaskSelect')?.value;

        if (!path) {
            alert('Please specify a dataset directory path.');
            return;
        }

        const manifestName = `${adapter}_${task}_manifest.json`;

        try {
            const res = await fetch('/api/v1/datasets/create_manifest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    adapter: adapter,
                    dataset_path: path,
                    manifest_name: manifestName,
                    task: task
                })
            });

            if (!res.ok) {
                const err = await res.json();
                alert(`Error creating manifest: ${err.detail}`);
                return;
            }

            const data = await res.json();
            alert(`Manifest successfully created at ${data.manifest_path} (${data.total_samples} samples)`);
            this.currentManifestPath = data.manifest_path;
            await this.loadManifests();

            // Auto-select in training dropdown
            const manifestSelect = document.getElementById('trainManifestSelect');
            if (manifestSelect) manifestSelect.value = data.manifest_path;

        } catch (err) {
            alert(`Manifest creation failed: ${err.message}`);
        }
    }

    async startTraining() {
        const task = document.getElementById('trainTaskSelect')?.value;
        const modelId = document.getElementById('trainModelIdInput')?.value.trim();
        const manifestPath = document.getElementById('trainManifestSelect')?.value;
        const epochs = parseInt(document.getElementById('trainEpochsInput')?.value || '10', 10);
        const batchSize = parseInt(document.getElementById('trainBatchSizeInput')?.value || '16', 10);
        const hiddenDim = parseInt(document.getElementById('trainHiddenDimInput')?.value || '128', 10);
        const lr = parseFloat(document.getElementById('trainLrInput')?.value || '0.001');

        if (!modelId) {
            alert('Please enter a unique Model ID.');
            return;
        }
        if (!manifestPath) {
            alert('Please select a training manifest.');
            return;
        }

        const payload = {
            task: task,
            model_id: modelId,
            dataset_adapter: document.getElementById('datasetAdapterSelect')?.value || 'custom',
            manifest_path: manifestPath,
            checkpoint_dir: `checkpoints/${modelId}`,
            model_architecture: task === 'isolated_sign' ? 'BiGRU_Attention_Classifier' : (task === 'continuous_gloss' ? 'BiGRU_CTC_GlossRecognizer' : 'GlossRecognizer_Translation_Pipeline'),
            input_dim: 144,
            sequence_length: task === 'isolated_sign' ? 30 : 60,
            hidden_dim: hiddenDim,
            num_layers: 2,
            dropout: 0.3,
            batch_size: batchSize,
            epochs: epochs,
            learning_rate: lr,
            weight_decay: 0.0001,
            patience: 5,
            random_seed: 42,
            device: 'cpu'
        };

        try {
            const res = await fetch('/api/v1/training/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const err = await res.json();
                alert(`Cannot start training: ${JSON.stringify(err.detail)}`);
                return;
            }

            // Start polling status
            this.toggleTrainingUI(true);
            this.pollTrainingStatus();

        } catch (err) {
            alert(`Training launch error: ${err.message}`);
        }
    }

    async cancelTraining() {
        try {
            await fetch('/api/v1/training/cancel', { method: 'POST' });
        } catch (err) {
            console.error('Cancel request failed:', err);
        }
    }

    pollTrainingStatus() {
        if (this.trainingPollTimer) clearInterval(this.trainingPollTimer);

        this.trainingPollTimer = setInterval(async () => {
            try {
                const res = await fetch('/api/v1/training/status');
                if (!res.ok) return;
                const status = await res.json();
                this.updateTrainingUI(status);

                if (status.state === 'completed' || status.state === 'failed' || status.state === 'cancelled') {
                    clearInterval(this.trainingPollTimer);
                    this.trainingPollTimer = null;
                    this.toggleTrainingUI(false);
                    this.loadRegisteredModels();
                }
            } catch (err) {
                console.warn('Status poll failed:', err);
            }
        }, 1200);
    }

    updateTrainingUI(status) {
        const stateEl = document.getElementById('trainingJobStateBadge');
        const progressFill = document.getElementById('trainingProgressBarFill');
        const epochText = document.getElementById('trainingEpochText');
        const lossText = document.getElementById('trainingLossText');
        const terminalEl = document.getElementById('trainingTerminalLogs');

        if (stateEl) {
            stateEl.textContent = status.state.toUpperCase();
            stateEl.className = `status-pill ${status.state}`;
        }

        if (progressFill && status.total_epochs > 0) {
            const pct = Math.round((status.current_epoch / status.total_epochs) * 100);
            progressFill.style.width = `${pct}%`;
        }

        if (epochText) {
            epochText.textContent = `Epoch: ${status.current_epoch} / ${status.total_epochs}`;
        }

        if (lossText) {
            lossText.textContent = `Train Loss: ${status.train_loss || 0} | Val Loss: ${status.val_loss || 0} | Val Acc: ${status.val_acc || 0}`;
        }

        if (terminalEl && status.logs) {
            terminalEl.textContent = status.logs.join('\n');
            terminalEl.scrollTop = terminalEl.scrollHeight;
        }
    }

    toggleTrainingUI(isRunning) {
        const startBtn = document.getElementById('startTrainingBtn');
        const cancelBtn = document.getElementById('cancelTrainingBtn');
        if (startBtn) startBtn.disabled = isRunning;
        if (cancelBtn) cancelBtn.disabled = !isRunning;
    }

    async loadRegisteredModels() {
        const tableBody = document.getElementById('modelsTableBody');
        if (!tableBody) return;

        try {
            const res = await fetch('/api/v1/models/');
            if (!res.ok) return;
            const models = await res.json();

            tableBody.innerHTML = '';
            if (models.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="7">No registered models found.</td></tr>';
                return;
            }

            models.forEach(m => {
                const tr = document.createElement('tr');
                const evalMetrics = m.evaluation_metrics ? JSON.stringify(m.evaluation_metrics) : 'Untested';
                const activeTag = m.is_active_for_task ? '<span class="badge badge-success">ACTIVE</span>' : '';

                tr.innerHTML = `
                    <td><strong>${m.model_id}</strong> ${activeTag}</td>
                    <td><span class="task-badge ${m.task}">${m.task}</span></td>
                    <td>${m.architecture}</td>
                    <td>${m.num_classes} classes</td>
                    <td><code class="hash-code">${m.checksum_sha256?.substring(0, 10)}...</code></td>
                    <td>${evalMetrics}</td>
                    <td>
                        <button class="btn btn-sm btn-activate" data-id="${m.model_id}" data-task="${m.task}">
                            ⚡ Deploy to Webcam
                        </button>
                    </td>
                `;

                tr.querySelector('.btn-activate')?.addEventListener('click', () => {
                    this.deployModelToWebcam(m.model_id, m.task);
                });

                tableBody.appendChild(tr);
            });
        } catch (err) {
            console.warn('Failed loading models table:', err);
        }
    }

    async deployModelToWebcam(modelId, task) {
        try {
            const res = await fetch('/api/v1/models/select', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_id: modelId, task: task })
            });

            if (res.ok) {
                alert(`Model '${modelId}' successfully deployed as the active webcam model!`);
                // Switch to webcam tab
                document.querySelector('.nav-tab[data-tab="webcam"]')?.click();
            } else {
                const err = await res.json();
                alert(`Error: ${err.detail}`);
            }
        } catch (err) {
            alert(`Deploy failed: ${err.message}`);
        }
    }
}
