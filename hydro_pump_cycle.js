// ============================================================================
// Lettuce Grow Farmstand Smart Hydroponics Pump Controller (Shelly Gen4 mJS)
// Optimized for Palo Alto, CA Outdoor Climate with Automatic Seasonal Switching
// ============================================================================

// [1. Season Override Setting]
// "AUTO": Automatic based on month (Dec-Feb: Winter, Mar-Nov: Summer/Fall)
// Can be manually forced to "SUMMER_FALL" or "WINTER"
let SEASON_OVERRIDE = "AUTO";

// [2. Seasonal Profiles]
// Plan A: Summer/Fall (March - November) - Outdoor dry heat & high transpiration
let CONFIG_SUMMER_FALL = {
  name: "Summer/Fall Mode",
  day_on_sec: 3 * 60,       // Normal Day: 3 min ON
  day_off_sec: 15 * 60,     // Normal Day: 15 min OFF
  peak_on_sec: 2 * 60,      // Midday Peak (11:00~15:00): 2 min ON
  peak_off_sec: 8 * 60,     // Midday Peak (11:00~15:00): 8 min OFF
  night_on_sec: 1 * 60,     // Night: 1 min ON
  night_off_sec: 45 * 60,   // Night: 45 min OFF
  day_start_hour: 7,        // 07:00 Day starts
  peak_start_hour: 11,      // 11:00 Midday Peak starts
  peak_end_hour: 15,        // 15:00 Midday Peak ends
  night_start_hour: 21      // 21:00 Night starts
};

// Winter (December - February) - Rainy season anti-overwatering & root cold protection
let CONFIG_WINTER = {
  name: "Winter Mode",
  day_on_sec: 3 * 60,       // Day: 3 min ON
  day_off_sec: 35 * 60,     // Day: 35 min OFF (prevent waterlogging during rainy season)
  night_on_sec: 1 * 60,     // Night: 1 min ON
  night_off_sec: 90 * 60,   // Night: 90 min OFF (protect roots from cold night water)
  day_start_hour: 8,        // 08:00 Day starts (later winter sunrise)
  night_start_hour: 17      // 17:00 Night starts (earlier winter sunset)
};

// [3. Safety Protection]
// Force shut off if pump runs longer than 5 minutes continuously
let MAX_RUN_LIMIT_SEC = 5 * 60;

let timerHandle = null;
let safetyTimer = null;
let cycleCount = 0;

// Calculate current month (1-12) from Unix timestamp using civil calendar arithmetic
function getMonthFromUnix(ts, utcOffsetSec) {
  let offset = (utcOffsetSec !== undefined) ? utcOffsetSec : -25200;
  let z = Math.floor((ts + offset) / 86400) + 719468;
  let era = Math.floor(z / 146097);
  let doe = z - era * 146097;
  let yoe = Math.floor((doe - Math.floor(doe / 1460) + Math.floor(doe / 36524) - Math.floor(doe / 146096)) / 365);
  let doy = doe - (365 * yoe + Math.floor(yoe / 4) - Math.floor(yoe / 100));
  let mp = Math.floor((5 * doy + 2) / 153);
  let m = (mp < 10) ? (mp + 3) : (mp - 9);
  return m;
}

// Get the active seasonal profile
function getActiveProfile() {
  if (SEASON_OVERRIDE === "WINTER") return CONFIG_WINTER;
  if (SEASON_OVERRIDE === "SUMMER_FALL") return CONFIG_SUMMER_FALL;

  let sys = Shelly.getComponentStatus("sys");
  if (!sys || !sys.unixtime) {
    return CONFIG_SUMMER_FALL; // Fallback to Summer/Fall
  }

  let month = getMonthFromUnix(sys.unixtime, sys.utc_offset);
  // December, January, February -> Winter Mode
  if (month === 12 || month === 1 || month === 2) {
    return CONFIG_WINTER;
  }
  return CONFIG_SUMMER_FALL;
}

// Get current cycle phase (PEAK, DAY, or NIGHT)
function getCurrentPhase(profile) {
  let sys = Shelly.getComponentStatus("sys");
  if (!sys || !sys.time) {
    return { on_sec: profile.day_on_sec, off_sec: profile.day_off_sec, name: "DAY" };
  }
  let hour = JSON.parse(sys.time.split(":")[0]);

  // Midday peak heat window (e.g. 11:00 ~ 15:00)
  if (profile.peak_start_hour !== undefined && profile.peak_end_hour !== undefined) {
    if (hour >= profile.peak_start_hour && hour < profile.peak_end_hour) {
      return { on_sec: profile.peak_on_sec, off_sec: profile.peak_off_sec, name: "PEAK" };
    }
  }

  // Normal daytime window
  if (hour >= profile.day_start_hour && hour < profile.night_start_hour) {
    return { on_sec: profile.day_on_sec, off_sec: profile.day_off_sec, name: "DAY" };
  }

  // Nighttime window
  return { on_sec: profile.night_on_sec, off_sec: profile.night_off_sec, name: "NIGHT" };
}

// Stop Pump
function stopPump() {
  Shelly.call("Switch.Set", { id: 0, on: false });
  if (safetyTimer) {
    Timer.clear(safetyTimer);
    safetyTimer = null;
  }

  let profile = getActiveProfile();
  let phase = getCurrentPhase(profile);
  let offSec = phase.off_sec;

  print("[Farmstand] Pump OFF (" + profile.name + " " + phase.name + ") | Resting for: " + (offSec / 60) + " min");
  timerHandle = Timer.set(offSec * 1000, false, startPump);
}

// Start Pump
function startPump() {
  cycleCount = cycleCount + 1;
  Shelly.call("Switch.Set", { id: 0, on: true });

  let profile = getActiveProfile();
  let phase = getCurrentPhase(profile);
  let onSec = phase.on_sec;

  print("[Farmstand] #" + cycleCount + " Pump ON (" + profile.name + " " + phase.name + ") | Watering for: " + (onSec / 60) + " min");

  // Normal turn off timer
  timerHandle = Timer.set(onSec * 1000, false, stopPump);

  // Safety protection timer (force turn off if 5 min exceeded)
  safetyTimer = Timer.set(MAX_RUN_LIMIT_SEC * 1000, false, function() {
    print("[Farmstand] [WARNING] Maximum run duration exceeded! Force turning off pump for safety.");
    stopPump();
  });
}

// Startup log and immediately begin first watering cycle
let initialProfile = getActiveProfile();
print("==================================================");
print("[Farmstand] Smart Hydroponics Controller Started: " + initialProfile.name);
if (initialProfile.peak_start_hour !== undefined) {
  print("[Farmstand] Peak (11-15h): " + (initialProfile.peak_on_sec / 60) + "m ON / " + (initialProfile.peak_off_sec / 60) + "m OFF");
}
print("[Farmstand] Day: " + (initialProfile.day_on_sec / 60) + "m ON / " + (initialProfile.day_off_sec / 60) + "m OFF");
print("[Farmstand] Night: " + (initialProfile.night_on_sec / 60) + "m ON / " + (initialProfile.night_off_sec / 60) + "m OFF");
print("==================================================");

startPump();
