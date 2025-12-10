const API_BASE_URL = "";

let currentUser = null;

function showSection(sectionId) {
    document.querySelectorAll('.glass-panel').forEach(el => {
        el.classList.add('hidden-section');
        el.classList.remove('active-section');
    });
    document.getElementById(sectionId).classList.remove('hidden-section');
    document.getElementById(sectionId).classList.add('active-section');

    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('onclick').includes(sectionId)) {
            btn.classList.add('active');
        }
    });
}

function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.remove('hidden');
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

// User Profile Handling
document.getElementById('user-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = e.target.querySelector('button');
    submitBtn.textContent = "Saving...";
    submitBtn.disabled = true;

    const userData = {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        phone_number: document.getElementById('phone').value,
        location: document.getElementById('user-location').value,
        resume_path: document.getElementById('resume').value,
        skills: document.getElementById('skills').value,
        experience: document.getElementById('experience').value
    };

    try {
        const response = await fetch(`${API_BASE_URL}/users/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData)
        });

        if (response.ok) {
            currentUser = await response.json();
            showToast('Profile saved successfully!');
            // Save to local storage for persistence across reloads
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            showToast('Profile saved! Generating customized job search...');
            setTimeout(() => {
                showSection('search-section');
                // Auto-search logic: clear inputs and search
                document.getElementById('job-query').value = "";
                searchJobs();
            }, 1000)
        } else {
            const error = await response.json();
            if (response.status === 400 && error.detail === "Email already registered") {
                // If already registered, fetch the user
                const getResponse = await fetch(`${API_BASE_URL}/users/${userData.email}`);
                if (getResponse.ok) {
                    currentUser = await getResponse.json();
                    showToast('Welcome back! Profile loaded.');
                    localStorage.setItem('currentUser', JSON.stringify(currentUser));
                } else {
                    showToast('Error saving profile: ' + error.detail);
                }
            } else {
                showToast('Error saving profile: ' + (error.detail || 'Unknown error'));
            }
        }
    } catch (error) {
        showToast('Network error: ' + error.message);
    } finally {
        submitBtn.textContent = "Save Profile";
        submitBtn.disabled = false;
    }
});

// Load user from local storage on startup
window.addEventListener('load', () => {
    const storedUser = localStorage.getItem('currentUser');
    if (storedUser) {
        currentUser = JSON.parse(storedUser);
        document.getElementById('name').value = currentUser.name || '';
        document.getElementById('email').value = currentUser.email || '';
        document.getElementById('phone').value = currentUser.phone_number || '';
        document.getElementById('user-location').value = currentUser.location || '';
        document.getElementById('resume').value = currentUser.resume_path || '';
        document.getElementById('skills').value = currentUser.skills || '';
        document.getElementById('experience').value = currentUser.experience || '';

        // Auto-fill job search location from profile if not set
        if (currentUser.location) {
            document.getElementById('job-location').value = currentUser.location;
        }
        showToast(`Welcome back, ${currentUser.name}`);
        showSection('search-section');
    }
});


// Job Search
async function searchJobs() {
    const query = document.getElementById('job-query').value;
    const location = document.getElementById('job-location').value;
    const loading = document.getElementById('loading');
    const container = document.getElementById('jobs-container');

    // If no query and no user, warn. If user exists, we allow empty query (AI mode).
    if (!query && !currentUser) {
        showToast('Please enter a job title or log in for AI suggestions');
        return;
    }

    loading.classList.remove('hidden');
    container.innerHTML = '';

    try {
        let url = `${API_BASE_URL}/jobs/search?query=${encodeURIComponent(query)}&location=${encodeURIComponent(location)}`;
        if (currentUser && currentUser.id) {
            url += `&user_id=${currentUser.id}`;
        }

        const response = await fetch(url);
        const jobs = await response.json();

        loading.classList.add('hidden');

        if (jobs.length === 0) {
            container.innerHTML = '<p style="grid-column: 1/-1; text-align: center;">No jobs found.</p>';
            return;
        }

        jobs.forEach(job => {
            const card = document.createElement('div');
            card.className = 'job-card';
            card.innerHTML = `
                <div class="job-title">${job.title}</div>
                <div class="job-company">${job.company}</div>
                <div class="job-location">${job.location}</div>
                <p style="font-size: 0.9rem; color: #cbd5e1; margin-bottom: 1rem; flex-grow: 1;">
                    ${job.description.substring(0, 100)}...
                </p>
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                    <!-- Link removed as per user request -->
                </div>
                ${job.hr_email ?
                    `<button onclick="applyForJob(${job.id})" class="primary-btn">Easy Apply with AI</button>` :
                    `<a href="${job.url}" target="_blank" class="primary-btn" style="text-decoration: none; text-align: center; display: block;">Apply Manually</a>`
                }
            `;
            container.appendChild(card);
        });

    } catch (error) {
        loading.classList.add('hidden');
        showToast('Error searching jobs: ' + error.message);
    }
}

// Apply Logic
async function applyForJob(jobId) {
    if (!currentUser) {
        showToast('Please save your profile first before applying!');
        showSection('user-section');
        return;
    }

    showToast('AI Agent is generating your email...');

    const applicationData = {
        job_id: jobId
    };

    try {
        const response = await fetch(`${API_BASE_URL}/apply/?user_id=${currentUser.id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(applicationData)
        });

        if (response.ok) {
            const application = await response.json();

            if (application.status === 'manual_apply_required') {
                showToast(`Manual Application Required. Check 'Applications' tab.`);
            } else {
                showToast(`Application Sent! Status: ${application.status}`);
            }
            loadApplications(); // Refresh list
        } else {
            const error = await response.json();
            if (response.status === 404) {
                showToast('Error: Profile mismatch. Please Save Profile again.');
                showSection('user-section');
            } else {
                showToast('Application failed: ' + error.detail);
            }
        }
    } catch (error) {
        showToast('Network error: ' + error.message);
    }
}

// Load Applications
async function loadApplications() {
    if (!currentUser) return;

    const container = document.getElementById('applications-container');

    try {
        const response = await fetch(`${API_BASE_URL}/applications/${currentUser.id}`);
        const applications = await response.json();

        container.innerHTML = '';
        if (applications.length === 0) {
            container.innerHTML = '<p>No applications yet.</p>';
            return;
        }

        applications.forEach(app => {

            const jobTitle = app.job ? app.job.title : `Job #${app.job_id}`;
            const company = app.job ? app.job.company : '';

            let statusClass = 'status-pending';
            let statusText = app.status ? app.status.replace('_', ' ').toUpperCase() : 'UNKNOWN';

            if (app.status === 'email_sent') {
                statusClass = 'status-sent';
            } else if (app.status === 'manual_apply_required') {
                statusClass = 'status-manual';
            } else if (app.status === 'failed') {
                statusClass = 'status-failed';
            }

            let actionHtml = '';
            // Fix: Check where 'url' is located. Typically in app.job.url. 
            // If app.job is present.
            if (app.status === 'manual_apply_required' && app.job && app.job.url) {
                actionHtml = `<a href="${app.job.url}" target="_blank" class="manual-apply-btn">Apply Now ↗</a>`;
            }

            const item = document.createElement('div');
            item.className = 'app-item';
            item.innerHTML = `
                <div>
                    <div style="font-weight: 600; font-size: 1.1rem;">${jobTitle}</div>
                    <div style="color: #94a3b8; font-size: 0.9rem;">${company}</div>
                </div>
                <div style="display: flex; align-items: center;">
                    <div class="status-badge ${statusClass}">
                        ${statusText}
                    </div>
                    ${actionHtml}
                </div>
            `;
            container.appendChild(item);
        });
    } catch (error) {
        console.error('Error loading applications', error);
    }
}

// Load applications when section is clicked
document.querySelector('button[onclick="showSection(\'applied-section\')"]').addEventListener('click', loadApplications);
