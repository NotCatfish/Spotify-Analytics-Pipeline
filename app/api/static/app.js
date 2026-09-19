// State Machine Variables
let lastTrackId = null;
let lastStatus = "IDLE";
let lastDuration = 0.0;
let skipTimestamps = [];
let previousSongSkipped = false;
let reasonStart = "trackdone";
let sessionState = "IDLE";

function formatTime(seconds) {
    if (!seconds) return "0:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
}



async function fetchLiveQueue() {
    const nowTime = Date.now() / 1000;
    
    skipTimestamps = skipTimestamps.filter(t => nowTime - t <= 900);
    const skips3m = skipTimestamps.filter(t => nowTime - t <= 180).length;
    const skips15m = skipTimestamps.length;
    const secSinceSkip = skipTimestamps.length > 0 ? (nowTime - skipTimestamps[skipTimestamps.length - 1]) : 10000.0;

    const params = new URLSearchParams({
        queue_limit: 20,
        previous_song_skipped: previousSongSkipped,
        skips_last_3m: skips3m,
        skips_last_15m: skips15m,
        seconds_since_last_skip: secSinceSkip.toFixed(1),
        reason_start: reasonStart
    });

    try {
        const response = await fetch(`/predict/live-queue?${params.toString()}`);
        if (response.status === 401) {
            document.getElementById("last-event").innerText = "Authentication needed.";
            return;
        }
        
        const data = await response.json();
        if (data.status === "AUTH_REQUIRED") {
            window.location.href = data.auth_url || "/login";
            return;
        }
        processQueueData(data, nowTime, skips3m, secSinceSkip);
    } catch (error) {
        console.error("Fetch Error:", error);
    }
}

function processQueueData(data, nowTime, skips3m, secSinceSkip) {
    if (data.status === "IDLE") {
        if (lastStatus !== "IDLE") {
            lastStatus = "IDLE";
            lastTrackId = null;
            updateSessionState("IDLE");
            document.getElementById("current-track-card").style.display = "none";
            document.getElementById("queue-list").innerHTML = "<div style='color: var(--text-muted); text-align:center;'>Spotify is idle. Play a track to begin.</div>";
        }
        return;
    }

    if (data.status === "ACTIVE") {
        const currentTrack = data.currently_playing || {};
        const currId = currentTrack.id;
        const currProgress = currentTrack.progress_seconds || 0;
        const currDuration = currentTrack.duration_seconds || 180;
        
        const isTrackChange = (currId !== lastTrackId || lastStatus !== "ACTIVE");

        if (isTrackChange) {
            if (lastTrackId !== null) {
                const cutoff = lastDuration > 15.0 ? Math.max(10.0, lastDuration - 10.0) : 30.0;
                previousSongSkipped = true;
                reasonStart = "fwdbtn";
                skipTimestamps.push(nowTime);
                document.getElementById("last-event").innerText = `⚡ Skipped previous track`;
            } else {
                document.getElementById("last-event").innerText = "Session Active";
            }
        }

        if (!isTrackChange && currProgress >= 45.0) {
            previousSongSkipped = false;
            reasonStart = "trackdone";
            document.getElementById("last-event").innerText = `✓ Settled into track (${currProgress.toFixed(0)}s played)`;
        }

        if (skips3m >= 2 && currProgress < 45.0) {
            updateSessionState("SKIP_SPREE");
        } else if ((skips3m >= 1 || secSinceSkip < 45.0) && currProgress < 60.0) {
            updateSessionState("RESTLESS");
        } else {
            updateSessionState("CALM_FLOW");
        }

        // Update Current Track UI
        document.getElementById("current-track-card").style.display = "block";
        document.getElementById("ct-song").innerText = currentTrack.song_name || "Unknown";
        document.getElementById("ct-artist").innerText = currentTrack.artist_name || "Unknown Artist";
        document.getElementById("ct-skips").innerText = skips3m;
        
        document.getElementById("ct-progress-text").innerText = formatTime(currProgress);
        document.getElementById("ct-duration-text").innerText = formatTime(currDuration);
        
        const pct = Math.min(100, Math.max(0, (currProgress / currDuration) * 100));
        document.getElementById("ct-progress-bar").style.width = `${pct}%`;

        // Render Queue
        renderQueue(data.upcoming_queue_forecast || []);

        lastTrackId = currId;
        lastStatus = "ACTIVE";
        lastDuration = currDuration;
    }
}

function updateSessionState(state) {
    sessionState = state;
    const badge = document.getElementById("session-state");
    badge.innerText = state.replace("_", " ");
}

function renderQueue(forecast) {
    const list = document.getElementById("queue-list");
    list.innerHTML = "";
    
    if (forecast.length === 0) {
        list.innerHTML = "<div style='color: var(--text-muted); text-align:center;'>No upcoming tracks.</div>";
        return;
    }

    forecast.forEach(item => {
        const prob = item.skip_probability * 100;
        // Keep gold variants for the bars
        let color = "var(--accent)"; // gold
        if (prob >= 77.6) color = "var(--red)";

        const html = `
            <div class="queue-item">
                <div class="track-info">
                    <div class="track-name">#${item.queue_position} ${item.song_name}</div>
                    <div class="track-artist">${item.artist_name}</div>
                </div>
                <div class="prob-container">
                    <div style="font-weight: 800; color: ${color};">${prob.toFixed(1)}% Risk</div>
                    <div class="prob-bar-bg">
                        <div class="prob-bar-fill" style="width: ${prob}%; background-color: ${color};"></div>
                    </div>
                </div>
            </div>
        `;
        list.innerHTML += html;
    });
}

// Start
fetchLiveQueue();
setInterval(fetchLiveQueue, 2500);
