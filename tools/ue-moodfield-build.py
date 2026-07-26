"""Build Moodfield inside the UE 4.27 source project.

Run with:
    UE4Editor-Cmd.exe project/spark.uproject \
      -ExecutePythonScript=tools/ue-moodfield-build.py -unattended -nop4

The script is intentionally idempotent. It rebuilds the generated material and
adds the classifier bridge to a working copy of the proven Keyfield Pulse
actor/widget. Use it in a branch or disposable project checkout.
"""

import unreal


SOURCE_ROOT = "/Game/CPPRO/KeyfieldPulse"
TARGET_ROOT = "/Game/CPPRO/Moodfield"
MATERIAL_ROOT = TARGET_ROOT + "/Materials"
COLLECTION_PATH = MATERIAL_ROOT + "/MPC_Moodfield"
MATERIAL_PATH = MATERIAL_ROOT + "/M_MoodfieldSurface"

SCALAR_DEFAULTS = {
    "MoodGlobal": 0.18,
    "MoodTyping": 0.12,
    "MoodGame": 0.0,
    "MoodBurst": 0.0,
    "MoodRepeat": 0.0,
    "MoodLeft": 0.08,
    "MoodCenter": 0.08,
    "MoodRight": 0.08,
    "MoodMassLeft": 0.08,
    "MoodMassCenter": 0.08,
    "MoodMassRight": 0.08,
    "MoodWasdShare": 0.0,
    "MoodActivityMass": 0.12,
    "MoodAlphaShare": 0.0,
    "MoodNavShare": 0.0,
    "MoodAlphaLeftShare": 0.0,
    "MoodAlphaRightShare": 0.0,
    "MoodProseTopLeft": 0.0,
    "MoodProseTopRight": 0.0,
    "MoodProseMiddleLeft": 0.0,
    "MoodProseMiddleRight": 0.0,
    "MoodProseBottomLeft": 0.0,
    "MoodProseBottomRight": 0.0,
    "MoodCaps": 0.0,
    "MoodLastEvent": 0.0,
    "MoodEventClock": 0.0,
    "MoodKeyCode": -1.0,
    "MoodContactCode": -1.0,
    "MoodInterval": 1.0,
    "MoodTrail0Code": -1.0,
    "MoodTrail0Clock": 0.0,
    "MoodTrail1Code": -1.0,
    "MoodTrail1Clock": 0.0,
    "MoodTrail2Code": -1.0,
    "MoodTrail2Clock": 0.0,
}

SURFACE_CODE = r"""
float2 p = UV;
// Slate's UI Time is application-relative rather than UWorld-relative.  The
// classifier supplies MoodEventClock from GetAccurateRealTime so these values
// share the same epoch on the CPPRO runtime.
float age = max(0.0, TimeSeconds - MoodEventClock);
float globalHeat = saturate(MoodGlobal - age * 0.025);
// The original per-key classifier remains available for diagnostics, but it
// is intentionally not allowed to drive the palette: an isolated Space,
// Shift, or letter should never flip the surface into a game mood.  Activity
// and WASD share are slow rolling proportions from the long-memory bridge.
float typing = saturate(MoodActivityMass - age * 0.0025);
float gaming = saturate(MoodWasdShare - age * 0.0018);
float alphaShare = saturate(MoodAlphaShare - age * 0.0018);
float navShare = saturate(MoodNavShare - age * 0.0025);
float alphaLeftShare = saturate(MoodAlphaLeftShare - age * 0.0018);
float alphaRightShare = saturate(MoodAlphaRightShare - age * 0.0018);
float proseTopLeft = saturate(MoodProseTopLeft - age * 0.0015);
float proseTopRight = saturate(MoodProseTopRight - age * 0.0015);
float proseMiddleLeft = saturate(MoodProseMiddleLeft - age * 0.0015);
float proseMiddleRight = saturate(MoodProseMiddleRight - age * 0.0015);
float proseBottomLeft = saturate(MoodProseBottomLeft - age * 0.0015);
float proseBottomRight = saturate(MoodProseBottomRight - age * 0.0015);
float burst = saturate(MoodBurst - age * 0.18);
float repeatHeat = saturate(MoodRepeat - age * 0.08);
float gameEvidence = saturate((gaming - 0.30) * 3.15);
float navEvidence = saturate((navShare - 0.22) * 3.20);
float activityEvidence = saturate((typing - 0.08) * 4.00);
float proseEvidence = saturate((alphaShare - 0.16) * 2.20);
proseEvidence *= activityEvidence;
proseEvidence *= 1.0 - gameEvidence * 0.82;
proseEvidence *= 1.0 - navEvidence * 0.76;

// Three trigonometric evaluations drive the entire full-screen field.  The
// earlier nested-noise prototype was visually legible but too expensive on
// the CPPRO's Android GPU.  Everything else below uses additions,
// multiplications, abs, and saturate-friendly distance approximations.
float t = TimeSeconds;
float waveA = 0.5 + 0.5 * sin(p.x * 8.5 + p.y * 3.2 + t * 0.48);
float waveB = 0.5 + 0.5 * sin(p.y * 10.5 - p.x * 2.6 - t * 0.36);
float breathe = 0.5 + 0.5 * sin(t * (0.62 + globalHeat * 0.42));
float cells = saturate(waveA * 0.62 + waveB * 0.48 - 0.05);
float membranes = saturate(1.0 - abs(waveA - waveB) * 3.4);
membranes *= membranes;
float current = saturate(waveA * (1.0 - waveB) * 1.8);

// Convert the calibrated row-major CPPRO event number into the physical key
// center.  Moodfield owns the visible response now, so the substrate contact
// must begin beneath the actual key rather than relying on the inherited A2
// foreground rectangles to hide an approximate coordinate.
float keyX = 0.5;
float keyY = 0.5;
// MoodContactCode and MoodEventClock are committed by one press-only
// execution chain.  Classifier and release bookkeeping may continue changing
// independently without relocating an in-flight visible contact.
float keyCode = clamp(MoodContactCode, 0.0, 67.0);
if (keyCode < 16.0)
{
    if (keyCode < 13.0)
        keyX = (keyCode + 0.5) / 18.0;
    else if (keyCode < 14.0)
        keyX = 14.0 / 18.0;
    else
        keyX = (keyCode + 2.5) / 18.0;
    keyY = 0.09;
}
else if (keyCode < 32.0)
{
    float localKey = keyCode - 16.0;
    if (localKey < 1.0)
        keyX = 0.75 / 18.0;
    else if (localKey < 13.0)
        keyX = (localKey + 1.0) / 18.0;
    else if (localKey < 14.0)
        keyX = 14.25 / 18.0;
    else
        keyX = (localKey + 2.5) / 18.0;
    keyY = 0.285;
}
else if (keyCode < 45.0)
{
    float localKey = keyCode - 32.0;
    keyX = localKey < 1.0
        ? 0.875 / 18.0
        : (localKey < 12.0
            ? (localKey + 1.25) / 18.0
            : 13.875 / 18.0);
    keyY = 0.485;
}
else if (keyCode < 58.0)
{
    float localKey = keyCode - 45.0;
    keyX = localKey < 1.0
        ? 1.125 / 18.0
        : (localKey < 11.0
            ? (localKey + 1.75) / 18.0
            : (localKey < 12.0 ? 13.625 / 18.0 : 16.5 / 18.0));
    keyY = 0.685;
}
else
{
    float localKey = keyCode - 58.0;
    if (localKey < 3.0)
        keyX = (0.625 + localKey * 1.25) / 18.0;
    else if (localKey < 4.0)
        keyX = 6.875 / 18.0;
    else if (localKey < 5.0)
        keyX = 10.625 / 18.0;
    else if (localKey < 6.0)
        keyX = 11.875 / 18.0;
    else if (localKey < 7.0)
        keyX = 13.25 / 18.0;
    else
        keyX = (localKey + 8.5) / 18.0;
    keyY = 0.89;
}

// Treat a press as contact with a continuous membrane.  A soft depression
// forms beneath the key, a compressed rim catches the substrate light, and a
// shallow rebound wave travels into neighboring cells.  The aspect-adjusted
// distance is intentionally a little wider than one key so it cannot read as
// another rectangular per-key overlay.
float2 keyDelta = float2((p.x - keyX) / 0.078, (p.y - keyY) / 0.245);
float keyDistance = sqrt(max(dot(keyDelta, keyDelta), 0.0001));
float contactLife = saturate(1.0 - age * 3.15);
contactLife *= contactLife;
float reboundLife = saturate(1.0 - age * 1.22);
float keyBase = saturate(1.0 - keyDistance);
float contactDepth = keyBase * keyBase * contactLife;
float contactRim = saturate(1.0 - abs(keyDistance - 0.72) * 7.0);
contactRim *= contactRim * contactLife;
float waveRadius = 0.82 + age * 2.45;
float pressWave = saturate(
    1.0 - abs(keyDistance - waveRadius) * (3.8 - age * 1.2)
);
pressWave *= pressWave * reboundLife;
float keyHeat = saturate(contactRim * 0.72 + pressWave * 0.48);

// A short thermal memory makes usage form visible geography.  Repeated
// movement keys cluster into one warm mass; prose leaves a wider, cooler
// constellation.  Row-major coordinates are sufficient for these broad
// substrate marks because the exact calibrated lights remain above them.
float trail0Code = max(MoodTrail0Code, 0.0);
float2 trail0Pos = float2(0.5, 0.5);
if (trail0Code < 16.0)
{
    if (trail0Code < 13.0)
        trail0Pos.x = (trail0Code + 0.5) / 18.0;
    else if (trail0Code < 14.0)
        trail0Pos.x = 14.0 / 18.0;
    else
        trail0Pos.x = (trail0Code + 2.5) / 18.0;
    trail0Pos.y = 0.09;
}
else if (trail0Code < 32.0)
{
    float localTrail = trail0Code - 16.0;
    if (localTrail < 1.0)
        trail0Pos.x = 0.75 / 18.0;
    else if (localTrail < 13.0)
        trail0Pos.x = (localTrail + 1.0) / 18.0;
    else if (localTrail < 14.0)
        trail0Pos.x = 14.25 / 18.0;
    else
        trail0Pos.x = (localTrail + 2.5) / 18.0;
    trail0Pos.y = 0.285;
}
else if (trail0Code < 45.0)
{
    float localTrail = trail0Code - 32.0;
    trail0Pos.x = localTrail < 1.0
        ? 0.875 / 18.0
        : (localTrail < 12.0
            ? (localTrail + 1.25) / 18.0
            : 13.875 / 18.0);
    trail0Pos.y = 0.485;
}
else if (trail0Code < 58.0)
{
    float localTrail = trail0Code - 45.0;
    trail0Pos.x = localTrail < 1.0
        ? 1.125 / 18.0
        : (localTrail < 11.0
            ? (localTrail + 1.75) / 18.0
            : (localTrail < 12.0 ? 13.625 / 18.0 : 16.5 / 18.0));
    trail0Pos.y = 0.685;
}
else
{
    float localTrail = trail0Code - 58.0;
    if (localTrail < 3.0)
        trail0Pos.x = (0.625 + localTrail * 1.25) / 18.0;
    else if (localTrail < 4.0)
        trail0Pos.x = 6.875 / 18.0;
    else if (localTrail < 5.0)
        trail0Pos.x = 10.625 / 18.0;
    else if (localTrail < 6.0)
        trail0Pos.x = 11.875 / 18.0;
    else if (localTrail < 7.0)
        trail0Pos.x = 13.25 / 18.0;
    else
        trail0Pos.x = (localTrail + 8.5) / 18.0;
    trail0Pos.y = 0.89;
}
float trail0Age = max(0.0, TimeSeconds - MoodTrail0Clock);
float trail0Spread = 1.0 + min(trail0Age * 0.105, 1.35);
float2 trail0Delta = float2(
    (p.x - trail0Pos.x) / (0.24 * trail0Spread),
    (p.y - trail0Pos.y) / (0.44 * trail0Spread)
);
float trail0Base = saturate(1.0 - dot(trail0Delta, trail0Delta) * 0.58);
float trail0Heat = trail0Base * trail0Base
    * saturate(1.0 - trail0Age * 0.080)
    * step(0.0, MoodTrail0Code);

float trail1Code = max(MoodTrail1Code, 0.0);
float2 trail1Pos = float2(0.5, 0.5);
if (trail1Code < 16.0)
{
    if (trail1Code < 13.0)
        trail1Pos.x = (trail1Code + 0.5) / 18.0;
    else if (trail1Code < 14.0)
        trail1Pos.x = 14.0 / 18.0;
    else
        trail1Pos.x = (trail1Code + 2.5) / 18.0;
    trail1Pos.y = 0.09;
}
else if (trail1Code < 32.0)
{
    float localTrail = trail1Code - 16.0;
    if (localTrail < 1.0)
        trail1Pos.x = 0.75 / 18.0;
    else if (localTrail < 13.0)
        trail1Pos.x = (localTrail + 1.0) / 18.0;
    else if (localTrail < 14.0)
        trail1Pos.x = 14.25 / 18.0;
    else
        trail1Pos.x = (localTrail + 2.5) / 18.0;
    trail1Pos.y = 0.285;
}
else if (trail1Code < 45.0)
{
    float localTrail = trail1Code - 32.0;
    trail1Pos.x = localTrail < 1.0
        ? 0.875 / 18.0
        : (localTrail < 12.0
            ? (localTrail + 1.25) / 18.0
            : 13.875 / 18.0);
    trail1Pos.y = 0.485;
}
else if (trail1Code < 58.0)
{
    float localTrail = trail1Code - 45.0;
    trail1Pos.x = localTrail < 1.0
        ? 1.125 / 18.0
        : (localTrail < 11.0
            ? (localTrail + 1.75) / 18.0
            : (localTrail < 12.0 ? 13.625 / 18.0 : 16.5 / 18.0));
    trail1Pos.y = 0.685;
}
else
{
    float localTrail = trail1Code - 58.0;
    if (localTrail < 3.0)
        trail1Pos.x = (0.625 + localTrail * 1.25) / 18.0;
    else if (localTrail < 4.0)
        trail1Pos.x = 6.875 / 18.0;
    else if (localTrail < 5.0)
        trail1Pos.x = 10.625 / 18.0;
    else if (localTrail < 6.0)
        trail1Pos.x = 11.875 / 18.0;
    else if (localTrail < 7.0)
        trail1Pos.x = 13.25 / 18.0;
    else
        trail1Pos.x = (localTrail + 8.5) / 18.0;
    trail1Pos.y = 0.89;
}
float trail1Age = max(0.0, TimeSeconds - MoodTrail1Clock);
float trail1Spread = 1.0 + min(trail1Age * 0.090, 1.50);
float2 trail1Delta = float2(
    (p.x - trail1Pos.x) / (0.30 * trail1Spread),
    (p.y - trail1Pos.y) / (0.52 * trail1Spread)
);
float trail1Base = saturate(1.0 - dot(trail1Delta, trail1Delta) * 0.58);
float trail1Heat = trail1Base * trail1Base
    * saturate(1.0 - trail1Age * 0.060)
    * step(0.0, MoodTrail1Code);

float trail2Code = max(MoodTrail2Code, 0.0);
float2 trail2Pos = float2(0.5, 0.5);
if (trail2Code < 16.0)
{
    if (trail2Code < 13.0)
        trail2Pos.x = (trail2Code + 0.5) / 18.0;
    else if (trail2Code < 14.0)
        trail2Pos.x = 14.0 / 18.0;
    else
        trail2Pos.x = (trail2Code + 2.5) / 18.0;
    trail2Pos.y = 0.09;
}
else if (trail2Code < 32.0)
{
    float localTrail = trail2Code - 16.0;
    if (localTrail < 1.0)
        trail2Pos.x = 0.75 / 18.0;
    else if (localTrail < 13.0)
        trail2Pos.x = (localTrail + 1.0) / 18.0;
    else if (localTrail < 14.0)
        trail2Pos.x = 14.25 / 18.0;
    else
        trail2Pos.x = (localTrail + 2.5) / 18.0;
    trail2Pos.y = 0.285;
}
else if (trail2Code < 45.0)
{
    float localTrail = trail2Code - 32.0;
    trail2Pos.x = localTrail < 1.0
        ? 0.875 / 18.0
        : (localTrail < 12.0
            ? (localTrail + 1.25) / 18.0
            : 13.875 / 18.0);
    trail2Pos.y = 0.485;
}
else if (trail2Code < 58.0)
{
    float localTrail = trail2Code - 45.0;
    trail2Pos.x = localTrail < 1.0
        ? 1.125 / 18.0
        : (localTrail < 11.0
            ? (localTrail + 1.75) / 18.0
            : (localTrail < 12.0 ? 13.625 / 18.0 : 16.5 / 18.0));
    trail2Pos.y = 0.685;
}
else
{
    float localTrail = trail2Code - 58.0;
    if (localTrail < 3.0)
        trail2Pos.x = (0.625 + localTrail * 1.25) / 18.0;
    else if (localTrail < 4.0)
        trail2Pos.x = 6.875 / 18.0;
    else if (localTrail < 5.0)
        trail2Pos.x = 10.625 / 18.0;
    else if (localTrail < 6.0)
        trail2Pos.x = 11.875 / 18.0;
    else if (localTrail < 7.0)
        trail2Pos.x = 13.25 / 18.0;
    else
        trail2Pos.x = (localTrail + 8.5) / 18.0;
    trail2Pos.y = 0.89;
}
float trail2Age = max(0.0, TimeSeconds - MoodTrail2Clock);
float trail2Spread = 1.0 + min(trail2Age * 0.075, 1.65);
float2 trail2Delta = float2(
    (p.x - trail2Pos.x) / (0.36 * trail2Spread),
    (p.y - trail2Pos.y) / (0.62 * trail2Spread)
);
float trail2Base = saturate(1.0 - dot(trail2Delta, trail2Delta) * 0.58);
float trail2Heat = trail2Base * trail2Base
    * saturate(1.0 - trail2Age * 0.045)
    * step(0.0, MoodTrail2Code);
float historyHeat = saturate(
    trail0Heat * 0.18 + trail1Heat * 0.13 + trail2Heat * 0.09
);
// A stopped surface should remember its geography, cool, and then rest.  It
// should not resurrect a fully developed old basin on the first key after a
// long pause.  Freshness across the last three contacts provides a cheap
// sequence-depth signal: one new key only begins waking the retained map,
// while a short run of typing restores its full authority.
float trail0Fresh = saturate(1.0 - trail0Age * 0.80)
    * step(0.0, MoodTrail0Code);
float trail1Fresh = saturate(1.0 - trail1Age * 0.42)
    * step(0.0, MoodTrail1Code);
float trail2Fresh = saturate(1.0 - trail2Age * 0.28)
    * step(0.0, MoodTrail2Code);
float sequenceDepth = saturate(
    trail0Fresh * 0.22 + trail1Fresh * 0.31 + trail2Fresh * 0.47
);
float moodPersistence = saturate(
    1.0 - max(age - 3.50, 0.0) * 0.034
);
float moodReengagement = 0.30 + sequenceDepth * 0.70;
float moodCooling = saturate(max(age - 0.65, 0.0) * 0.095);
float moodActive = saturate(1.0 - age * 0.34);

float heartbeat = breathe * breathe;
heartbeat *= heartbeat;

float leftField = saturate(1.0 - abs(p.x - 0.23) / 0.25);
float centerField = saturate(1.0 - abs(p.x - 0.53) / 0.27);
float rightField = saturate(1.0 - abs(p.x - 0.84) / 0.18);
leftField *= leftField;
centerField *= centerField;
rightField *= rightField;
// These values are rolling usage memories, not instantaneous key signals.
// They integrate roughly the last fifty presses and therefore move slowly
// enough for the surface to establish a stable character.
float memoryFade = saturate(1.0 - age * 0.010);
float leftMemory = saturate(
    (MoodMassLeft * 0.80 + MoodLeft * 0.20) * memoryFade
);
float centerMemory = saturate(
    (MoodMassCenter * 0.80 + MoodCenter * 0.20) * memoryFade
);
float rightMemory = saturate(
    (MoodMassRight * 0.80 + MoodRight * 0.20) * memoryFade
);
float memoryTotal = leftMemory + centerMemory + rightMemory;
float memoryMass = saturate((memoryTotal - 0.12) * 1.08);
float dominantMemory = max(leftMemory, max(centerMemory, rightMemory));
float concentration = dominantMemory / max(memoryTotal, 0.12);
float clusterEvidence = saturate((concentration - 0.43) * 2.85);
clusterEvidence *= activityEvidence;
// Prose is not merely "a lot of alpha keys."  Ordinary QWERTY writing has a
// durable bilateral signature: both typing hands contribute over time.
// Compact controls are usually unilateral (WASD on the left, UHJK/IJKL on
// the right), and arrows are already identified independently.  This is a
// much stronger discriminator than treating the center-heavy letter field as
// spatially uniform.
float distribution = saturate((0.62 - concentration) * 4.20);
float bilateralMass = saturate(
    min(alphaLeftShare, alphaRightShare) * 4.40
);
float bilateralBalance = 1.0 - saturate(
    abs(alphaLeftShare - alphaRightShare)
    / max(alphaLeftShare + alphaRightShare, 0.08)
);
float proseConfidence = bilateralMass
    * (0.62 + bilateralBalance * 0.38);
float proseMode = proseEvidence * proseConfidence;
proseMode *= 0.72 + distribution * 0.28;
proseMode *= 1.0 - clusterEvidence * 0.42;
float proseCadence = saturate((0.46 - MoodInterval) * 2.35);
float proseEnergy = proseMode * (0.58 + proseCadence * 0.42);
// During prose, recent contacts become a pair of soft paths through the same
// membrane instead of three unrelated hot spots.  Pixel coordinates are
// aspect-corrected before measuring distance, so the paths have a consistent
// apparent width across the CPPRO's very wide display.  The frac-based pulse
// travels from the older key toward the newer one without adding expensive
// trigonometric work to the mobile shader.
float2 proseP = float2(p.x * 3.58, p.y);
float2 prose0 = float2(trail0Pos.x * 3.58, trail0Pos.y);
float2 prose1 = float2(trail1Pos.x * 3.58, trail1Pos.y);
float2 prose2 = float2(trail2Pos.x * 3.58, trail2Pos.y);
float2 proseV01 = prose0 - prose1;
float2 proseV12 = prose1 - prose2;
float proseH01 = saturate(
    dot(proseP - prose1, proseV01)
    / max(dot(proseV01, proseV01), 0.0001)
);
float proseH12 = saturate(
    dot(proseP - prose2, proseV12)
    / max(dot(proseV12, proseV12), 0.0001)
);
float proseD01 = length(proseP - (prose1 + proseV01 * proseH01));
float proseD12 = length(proseP - (prose2 + proseV12 * proseH12));
float prosePath01 = saturate(1.0 - proseD01 / 0.060);
float prosePath12 = saturate(1.0 - proseD12 / 0.072);
prosePath01 *= prosePath01
    * saturate(1.0 - trail0Age * 0.72)
    * step(0.0, MoodTrail1Code);
prosePath12 *= prosePath12
    * saturate(1.0 - trail1Age * 0.44)
    * step(0.0, MoodTrail2Code);
float proseTravel01 = 1.0 - abs(
    frac(proseH01 * 2.10 - t * (0.72 + proseCadence * 1.15)) * 2.0 - 1.0
);
float proseTravel12 = 1.0 - abs(
    frac(proseH12 * 1.65 - t * (0.46 + proseCadence * 0.82)) * 2.0 - 1.0
);
proseTravel01 *= proseTravel01;
proseTravel12 *= proseTravel12;
float proseFlow = saturate(
    prosePath01 * (0.46 + proseTravel01 * 0.54)
    + prosePath12 * (0.32 + proseTravel12 * 0.40)
) * proseEnergy;

// Six slow usage memories give prose the same spatial authority that WASD
// already has.  They follow the left/right halves of the three alpha rows,
// overlap softly, and are normalized against the busiest region.  A paragraph
// therefore grows a multi-lobed heat geography instead of merely tinting the
// whole substrate purple.
float proseLeftColumn = saturate(1.0 - abs(p.x - 0.285) / 0.235);
float proseRightColumn = saturate(1.0 - abs(p.x - 0.625) / 0.245);
float proseTopRow = saturate(1.0 - abs(p.y - 0.285) / 0.145);
float proseMiddleRow = saturate(1.0 - abs(p.y - 0.485) / 0.145);
float proseBottomRow = saturate(1.0 - abs(p.y - 0.685) / 0.145);
proseLeftColumn *= proseLeftColumn;
proseRightColumn *= proseRightColumn;
proseTopRow *= proseTopRow;
proseMiddleRow *= proseMiddleRow;
proseBottomRow *= proseBottomRow;
float proseZoneMax = max(
    max(proseTopLeft, proseTopRight),
    max(
        max(proseMiddleLeft, proseMiddleRight),
        max(proseBottomLeft, proseBottomRight)
    )
);
float proseZoneScale = 1.0 / max(proseZoneMax, 0.055);
float proseZoneShape = saturate((
    proseTopRow * (
        proseLeftColumn * proseTopLeft
        + proseRightColumn * proseTopRight
    )
    + proseMiddleRow * (
        proseLeftColumn * proseMiddleLeft
        + proseRightColumn * proseMiddleRight
    )
    + proseBottomRow * (
        proseLeftColumn * proseBottomLeft
        + proseRightColumn * proseBottomRight
    )
) * proseZoneScale);
// The zone memories only receive alpha keys, so they are already a reliable
// source for a typing map.  Do not multiply them by proseMode a second time:
// that made a valid map nearly invisible.  A confident WASD/nav classifier
// still yields visual ownership cleanly when those modes take over.
float proseMapEvidence = saturate((alphaShare - 0.05) * 3.60);
proseMapEvidence *= 1.0 - gameEvidence * 0.88;
proseMapEvidence *= 1.0 - navEvidence * 0.72;
proseMapEvidence *= moodPersistence * moodReengagement;
float proseZoneMap = proseZoneShape * proseMapEvidence;
float proseZoneCore = proseZoneShape * proseZoneShape * proseMapEvidence;
// The six zones are samples, not the final shape.  Collapse their weighted
// distribution into a live centroid and variance, then render one envelope
// around the entire pattern.  This is what lets a repeated word read as a
// region in the same way that the dedicated WASD detector already does.
float proseZoneTotal = max(
    proseTopLeft + proseTopRight
    + proseMiddleLeft + proseMiddleRight
    + proseBottomLeft + proseBottomRight,
    0.001
);
float proseLeftTotal =
    proseTopLeft + proseMiddleLeft + proseBottomLeft;
float proseRightTotal =
    proseTopRight + proseMiddleRight + proseBottomRight;
float proseCentroidX = (
    proseLeftTotal * 0.285 + proseRightTotal * 0.625
) / proseZoneTotal;
float proseCentroidY = (
    (proseTopLeft + proseTopRight) * 0.285
    + (proseMiddleLeft + proseMiddleRight) * 0.485
    + (proseBottomLeft + proseBottomRight) * 0.685
) / proseZoneTotal;
float proseLeftOffset = 0.285 - proseCentroidX;
float proseRightOffset = 0.625 - proseCentroidX;
float proseTopOffset = 0.285 - proseCentroidY;
float proseMiddleOffset = 0.485 - proseCentroidY;
float proseBottomOffset = 0.685 - proseCentroidY;
float proseVarianceX = (
    proseLeftTotal * proseLeftOffset * proseLeftOffset
    + proseRightTotal * proseRightOffset * proseRightOffset
) / proseZoneTotal;
float proseVarianceY = (
    (proseTopLeft + proseTopRight) * proseTopOffset * proseTopOffset
    + (proseMiddleLeft + proseMiddleRight)
        * proseMiddleOffset * proseMiddleOffset
    + (proseBottomLeft + proseBottomRight)
        * proseBottomOffset * proseBottomOffset
) / proseZoneTotal;
float proseBasinRadiusX = 0.105 + sqrt(proseVarianceX) * 1.35;
float proseBasinRadiusY = 0.130 + sqrt(proseVarianceY) * 1.18;
float2 proseBasinDelta = float2(
    (p.x - proseCentroidX) / proseBasinRadiusX,
    (p.y - proseCentroidY) / proseBasinRadiusY
);
float proseBasinDistance = dot(proseBasinDelta, proseBasinDelta);
// The low-frequency substrate currents perturb the envelope edge just enough
// to keep it alive.  The centroid and variance still come only from typing,
// so this motion cannot drag the mood map away from its accumulated region.
float proseBasinEdge = (waveA - 0.5) * 0.095
    + (waveB - 0.5) * 0.070;
float proseBasin = saturate(
    1.0 - proseBasinDistance * 0.58 + proseBasinEdge
);
proseBasin *= proseBasin;
float proseBasinEvidence = saturate(
    (proseZoneTotal - 0.03) * 2.80
) * proseMapEvidence;
float proseBasinMap = proseBasin * proseBasinEvidence;
float proseBasinCore = proseBasin * proseBasin * proseBasinEvidence;
float proseBasinHalo = saturate(
    1.0 - proseBasinDistance * 0.34 + proseBasinEdge * 0.45
);
proseBasinHalo = saturate(proseBasinHalo - proseBasin * 0.72)
    * proseBasinEvidence;

float leftWins = step(centerMemory, leftMemory)
    * step(rightMemory, leftMemory);
float centerWins = step(leftMemory, centerMemory)
    * step(rightMemory, centerMemory);
float rightWins = step(leftMemory, rightMemory)
    * step(centerMemory, rightMemory);
float clusterField =
    leftWins * leftField
    + centerWins * centerField
    + rightWins * rightField;
float3 clusterColor =
    leftWins * float3(0.720, 0.190, 0.018)
    + centerWins * float3(0.610, 0.040, 0.360)
    + rightWins * float3(0.025, 0.480, 0.500);

float wasdX = (p.x - 0.27) / 0.16;
float wasdY = (p.y - 0.58) / 0.25;
float wasdField = saturate(
    1.0 - (wasdX * wasdX + wasdY * wasdY) * 0.62
) * gameEvidence;
wasdField *= wasdField;

float proseBand = saturate(
    1.0 - abs(p.y - 0.50) / 0.36
) * proseMode;
proseBand *= proseBand;

float3 abyss = float3(0.008, 0.020, 0.075);
float3 deepTeal = float3(0.015, 0.255, 0.340);
float3 electricCyan = float3(0.035, 0.720, 0.760);
float3 violet = float3(0.370, 0.035, 0.580);

float3 color = lerp(abyss, deepTeal, 0.24 + cells * 0.66);
color = lerp(color, violet, saturate((1.0 - cells) * 0.30 + current * 0.12));
color += membranes * electricCyan * (0.16 + 0.20 * breathe);
float heartX = saturate(1.0 - abs(p.x - 0.50) / 0.48);
float heartY = saturate(1.0 - abs(p.y - 0.52) / 0.58);
color += heartbeat * heartX * heartX * heartY * heartY
    * float3(0.025, 0.115, 0.160);

float proseDrift = saturate(
    cells * 0.45 + current * 0.25 + waveB * 0.20 + p.x * 0.10
);
float3 proseColor = lerp(
    float3(0.210, 0.025, 0.360),
    float3(0.780, 0.205, 0.020),
    saturate(proseDrift * 0.84 + proseCadence * 0.16)
);
float3 proseFlowColor = lerp(
    float3(0.025, 0.420, 0.500),
    float3(0.940, 0.245, 0.025),
    saturate(p.x * 0.54 + proseTravel01 * 0.28 + proseCadence * 0.18)
);
float3 proseMapColor = lerp(
    float3(0.018, 0.500, 0.570),
    float3(1.000, 0.210, 0.012),
    saturate(proseZoneShape * 0.80 + proseCadence * 0.15 + current * 0.05)
);
float3 proseBasinActiveColor = lerp(
    float3(0.030, 0.355, 0.560),
    float3(1.000, 0.175, 0.010),
    saturate(proseBasin * 0.72 + proseCadence * 0.20 + current * 0.08)
);
float3 proseBasinRestColor = lerp(
    float3(0.025, 0.250, 0.455),
    float3(0.405, 0.030, 0.640),
    saturate(cells * 0.58 + waveB * 0.24 + p.x * 0.18)
);
float3 proseBasinColor = lerp(
    proseBasinActiveColor,
    proseBasinRestColor,
    moodCooling
);
float3 gameColor = lerp(
    float3(0.050, 0.570, 0.180),
    float3(1.000, 0.310, 0.018),
    saturate(historyHeat * 0.70 + current * 0.30)
);
float3 navColor = lerp(
    float3(0.018, 0.420, 0.520),
    float3(0.740, 0.410, 0.025),
    saturate(waveB * 0.64 + rightField * 0.36)
);

float3 leftMoodColor = lerp(
    float3(0.010, 0.330, 0.300),
    float3(0.620, 0.180, 0.018),
    gameEvidence * 0.78
);
float3 centerMoodColor = lerp(
    float3(0.245, 0.040, 0.390),
    float3(0.230, 0.410, 0.055),
    gameEvidence * 0.62
);
float3 rightMoodColor = lerp(
    float3(0.030, 0.175, 0.470),
    float3(0.035, 0.320, 0.285),
    gameEvidence * 0.48
);
float3 regionalMood =
    leftField * leftMemory * leftMoodColor
    + centerField * centerMemory * centerMoodColor
    + rightField * rightMemory * rightMoodColor;
float3 ambientMood = (
    leftMemory * leftMoodColor
    + centerMemory * centerMoodColor
    + rightMemory * rightMoodColor
) / max(memoryTotal, 0.12);

// The prose palette illuminates the existing material instead of replacing
// it.  The paths below then make the user's cadence and hand travel readable
// as one continuous behavior rather than a sequence of independent flashes.
color = lerp(
    color,
    color * 0.68 + proseColor * 0.52,
    proseMode * 0.24
);
color = lerp(color, navColor, navEvidence * 0.52);
color = lerp(color, gameColor, gameEvidence * 0.24);
color = lerp(
    color,
    gameColor,
    saturate(wasdField * 0.70 + historyHeat * gameEvidence * 0.58)
);

// Regional memory colors broad areas; its weighted average gently biases the
// entire field.  Individual contacts can therefore disappear while the mood
// they contributed remains visible and continues breathing.
color = lerp(
    color,
    color * 0.76 + ambientMood * 0.42,
    memoryMass * 0.32
);
color += regionalMood * (0.46 + 0.14 * breathe);
// Unlike the subdued global prose tint, this is the actual accumulated mood
// map.  Multiple active regions coexist, and their cores warm as cadence and
// repeated use increase.
color = lerp(
    color,
    color * 0.48 + proseMapColor * 0.88,
    proseZoneMap * 0.88
);
color += proseZoneCore * proseMapColor * (0.40 + membranes * 0.20);
// The weighted basin visually binds the active samples into one pattern.
// Individual key contacts remain readable above it, but they no longer have
// to carry the meaning of a repeated word by themselves.
color = lerp(
    color,
    color * 0.44 + proseBasinColor * 0.94,
    proseBasinMap * 0.82
);
color += proseBasinCore * proseBasinColor
    * (0.30 + membranes * 0.16 + moodActive * 0.12);
// A dim, cool outer membrane remains after the hot center subsides.  This
// makes decay visible as a state transition instead of a simple opacity fade.
color += proseBasinHalo * lerp(
    float3(0.015, 0.255, 0.390),
    float3(0.260, 0.025, 0.460),
    moodCooling
) * (0.10 + membranes * 0.08);
// Any sustained compact control group can now establish a focused mood.
// WASD is one example, not a privileged coordinate set: UHJK, IJKL, arrows,
// or another concentrated group raises the same regional concentration term.
color = lerp(
    color,
    color * 0.70 + clusterColor * 0.50,
    clusterEvidence * 0.38
);
color += clusterField * clusterEvidence * clusterColor
    * (0.36 + 0.10 * breathe);
color += historyHeat * lerp(
    float3(0.025, 0.130, 0.180),
    float3(0.340, 0.145, 0.012),
    gameEvidence
);
color += proseFlow * proseFlowColor * (0.34 + membranes * 0.20);
color += proseEnergy * membranes * proseColor * 0.085;
color += wasdField * float3(0.16, 0.34, 0.055);
color += proseBand * float3(0.035, 0.090, 0.125);
color += repeatHeat * (0.45 + 0.55 * waveA) * keyBase
    * float3(0.055, 0.012, 0.042);
float pressWarmth = saturate(0.62 - MoodInterval) * 1.65;
float3 pressColor = lerp(
    float3(0.020, 0.310, 0.355),
    float3(0.610, 0.205, 0.014),
    pressWarmth
);
// The dark center is the depth cue; the rim and rebound wave are reflections
// inside the same surface, not a new object drawn on top of it.
color *= 1.0 - contactDepth * (0.22 + membranes * 0.06);
color += contactDepth * current * pressColor * 0.12;
color += keyHeat * pressColor * (0.16 + membranes * 0.10);

float capsX = saturate(1.0 - abs(p.x - 0.055) / 0.045);
float capsY = saturate(1.0 - abs(p.y - 0.505) / 0.105);
float capsField = capsX * capsX * capsY * capsY;
color += capsField * MoodCaps * float3(1.0, 0.58, 0.06);

color *= 0.82 + 0.14 * breathe + 0.08 * globalHeat;
return saturate(color);
"""


def ensure_duplicate(source: str, target: str) -> None:
    if unreal.EditorAssetLibrary.does_asset_exist(target):
        unreal.log("Moodfield asset already exists: {}".format(target))
        return

    if not unreal.EditorAssetLibrary.duplicate_asset(source, target):
        raise RuntimeError("Could not duplicate {} to {}".format(source, target))

    unreal.log("Created Moodfield asset: {}".format(target))


def ensure_collection() -> unreal.MaterialParameterCollection:
    collection = None
    if unreal.EditorAssetLibrary.does_asset_exist(COLLECTION_PATH):
        collection = unreal.EditorAssetLibrary.load_asset(COLLECTION_PATH)
    if collection:
        existing = {
            str(parameter.get_editor_property("parameter_name"))
            for parameter in collection.get_editor_property("scalar_parameters")
        }
        scalar_parameters = list(
            collection.get_editor_property("scalar_parameters")
        )
        changed = False
        for name, default_value in SCALAR_DEFAULTS.items():
            if name in existing:
                continue
            parameter = unreal.CollectionScalarParameter()
            parameter.set_editor_property("parameter_name", name)
            parameter.set_editor_property("default_value", default_value)
            scalar_parameters.append(parameter)
            changed = True
        if changed:
            collection.set_editor_property(
                "scalar_parameters",
                scalar_parameters,
            )
            unreal.EditorAssetLibrary.save_loaded_asset(
                collection,
                only_if_is_dirty=False,
            )
        return collection

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    collection = tools.create_asset(
        "MPC_Moodfield",
        MATERIAL_ROOT,
        unreal.MaterialParameterCollection,
        unreal.MaterialParameterCollectionFactoryNew(),
    )
    if not collection:
        raise RuntimeError("Could not create {}".format(COLLECTION_PATH))

    scalar_parameters = []
    for name, default_value in SCALAR_DEFAULTS.items():
        parameter = unreal.CollectionScalarParameter()
        parameter.set_editor_property("parameter_name", name)
        parameter.set_editor_property("default_value", default_value)
        scalar_parameters.append(parameter)

    collection.set_editor_property("scalar_parameters", scalar_parameters)
    unreal.EditorAssetLibrary.save_loaded_asset(collection, only_if_is_dirty=False)
    unreal.log("Created Moodfield parameter collection.")
    return collection


def create_expression(material, expression_class, x, y):
    expression = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        expression_class,
        x,
        y,
    )
    if not expression:
        raise RuntimeError("Could not create {}".format(expression_class))
    return expression


def ensure_material(collection) -> unreal.Material:
    material = None
    if unreal.EditorAssetLibrary.does_asset_exist(MATERIAL_PATH):
        # UE 4.27's Python layer cannot read a material's protected expression
        # array, so rebuilding this generated asset is more reliable than
        # trying to patch it in place.  The stable object path is restored
        # immediately and consumers are configured after creation.
        if not unreal.EditorAssetLibrary.delete_asset(MATERIAL_PATH):
            raise RuntimeError(
                "Could not rebuild generated material {}".format(
                    MATERIAL_PATH
                )
            )

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = tools.create_asset(
        "M_MoodfieldSurface",
        MATERIAL_ROOT,
        unreal.Material,
        unreal.MaterialFactoryNew(),
    )
    if not material:
        raise RuntimeError("Could not create {}".format(MATERIAL_PATH))

    material.set_editor_property("material_domain", unreal.MaterialDomain.MD_UI)
    # This is a background brush; child widgets and key effects render after
    # it.  Opaque avoids a full-screen mobile blend without obscuring them.
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)

    uv = create_expression(
        material,
        unreal.MaterialExpressionTextureCoordinate,
        -1200,
        -300,
    )
    time = create_expression(
        material,
        unreal.MaterialExpressionTime,
        -1200,
        -160,
    )

    custom = create_expression(
        material,
        unreal.MaterialExpressionCustom,
        100,
        -240,
    )
    custom.set_editor_property("code", SURFACE_CODE)
    custom.set_editor_property(
        "output_type",
        unreal.CustomMaterialOutputType.CMOT_FLOAT3,
    )

    input_names = ["UV", "TimeSeconds"] + list(SCALAR_DEFAULTS.keys())
    custom_inputs = []
    for name in input_names:
        custom_input = unreal.CustomInput()
        custom_input.set_editor_property("input_name", name)
        custom_inputs.append(custom_input)
    custom.set_editor_property("inputs", custom_inputs)

    unreal.MaterialEditingLibrary.connect_material_expressions(
        uv,
        "",
        custom,
        "UV",
    )
    unreal.MaterialEditingLibrary.connect_material_expressions(
        time,
        "",
        custom,
        "TimeSeconds",
    )

    y = 20
    for name in SCALAR_DEFAULTS:
        expression = create_expression(
            material,
            unreal.MaterialExpressionCollectionParameter,
            -650,
            y,
        )
        expression.set_editor_property("collection", collection)
        expression.set_editor_property("parameter_name", name)
        unreal.MaterialEditingLibrary.connect_material_expressions(
            expression,
            "",
            custom,
            name,
        )
        y += 120

    unreal.MaterialEditingLibrary.connect_material_property(
        custom,
        "",
        unreal.MaterialProperty.MP_EMISSIVE_COLOR,
    )
    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    unreal.log("Created Moodfield surface material.")
    return material


def main() -> None:
    collection = ensure_collection()
    ensure_material(collection)
    if not unreal.MoodfieldAuthoringLibrary.configure_moodfield_runtime_assets():
        raise RuntimeError("Could not configure Moodfield runtime assets.")
    unreal.EditorAssetLibrary.save_directory(TARGET_ROOT, only_if_is_dirty=False)
    unreal.EditorAssetLibrary.save_directory(
        SOURCE_ROOT,
        only_if_is_dirty=False,
    )
    unreal.log("Moodfield runtime assets are ready.")


if __name__ == "__main__":
    main()
