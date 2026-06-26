<script setup>
// Floating phone mockups of the real app — used on the marketing landing hero and,
// in `single` mode, beside the sign-in form so the auth screen previews the app too.
// Keyframes (float-a/b/c, pulse-orb, scan-line, blink, streak-pulse) live in style.css
// so the inline `animation:` references resolve globally and honor reduced-motion/fx-off.
defineProps({
  // `single` shows just the centered Events phone (compact, for the auth hero column).
  single: { type: Boolean, default: false },
})
</script>

<template>
  <div class="app-preview" style="display:flex;align-items:flex-end;justify-content:center;gap:28px;position:relative;">

    <!-- ── Phone 1: Home screen ── (hidden in single mode and on narrow screens) -->
    <div v-if="!single" class="ap-side" style="animation:float-a 6s ease-in-out infinite;filter:drop-shadow(0 0 36px rgba(0,212,193,0.45)) drop-shadow(0 32px 48px rgba(0,0,0,0.9));">
      <div style="width:258px;border-radius:44px;background:#0e1020;border:2px solid rgba(0,212,193,0.35);overflow:hidden;position:relative;">
        <div style="position:absolute;top:0;left:50%;transform:translateX(-50%);width:100px;height:28px;background:#090b13;border-radius:0 0 20px 20px;z-index:10;display:flex;align-items:center;justify-content:center;gap:6px;">
          <div style="width:8px;height:8px;border-radius:50%;background:#181a28;"></div>
          <div style="width:46px;height:8px;border-radius:4px;background:#181a28;"></div>
        </div>
        <div style="padding:36px 0 0;background:radial-gradient(ellipse at 50% 40%, #1e1635 0%, #0d0f1c 100%);min-height:480px;position:relative;overflow:hidden;">
          <div style="position:absolute;left:14px;top:120px;font-size:22px;font-weight:700;color:rgba(255,255,255,0.05);font-family:monospace;">&lt;/&gt;</div>
          <div style="position:absolute;right:16px;bottom:100px;font-size:20px;font-weight:700;color:rgba(255,255,255,0.04);font-family:monospace;">{ }</div>
          <div style="display:flex;justify-content:space-between;padding:4px 18px 10px;font-size:10px;color:rgba(255,255,255,0.4);">
            <span>9:41</span>
            <div style="display:flex;gap:4px;align-items:center;">
              <svg width="12" height="10" viewBox="0 0 12 10"><rect x="0" y="4" width="2" height="6" fill="rgba(255,255,255,0.5)" rx="1"></rect><rect x="3" y="2" width="2" height="8" fill="rgba(255,255,255,0.5)" rx="1"></rect><rect x="6" y="0" width="2" height="10" fill="rgba(255,255,255,0.7)" rx="1"></rect><rect x="9" y="0" width="2" height="10" fill="rgba(255,255,255,0.7)" rx="1"></rect></svg>
              <svg width="14" height="10" viewBox="0 0 14 10"><rect x="0.5" y="0.5" width="11" height="9" rx="2" stroke="rgba(255,255,255,0.4)" stroke-width="1" fill="none"></rect><rect x="12" y="3" width="2" height="4" rx="1" fill="rgba(255,255,255,0.4)"></rect><rect x="1.5" y="1.5" width="7" height="7" rx="1.5" fill="rgba(255,255,255,0.7)"></rect></svg>
            </div>
          </div>
          <div style="display:flex;align-items:flex-start;justify-content:space-between;padding:0 16px 8px;">
            <div>
              <div style="font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:800;color:#fff;line-height:1.2;">Hey, Pablo 👑</div>
              <div style="font-size:11px;color:rgba(255,255,255,0.4);margin-top:2px;">7 new badges this week</div>
            </div>
            <div style="width:36px;height:36px;border-radius:10px;background:#fff;display:flex;align-items:center;justify-content:center;position:relative;">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" fill="#0097a7"></path><path d="M8 12l3 3 5-5" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path></svg>
              <div style="position:absolute;bottom:-4px;right:-4px;width:14px;height:14px;border-radius:50%;background:#0d0f1c;border:1px solid rgba(255,255,255,0.2);display:flex;align-items:center;justify-content:center;">
                <svg width="8" height="8" viewBox="0 0 24 24" fill="rgba(255,255,255,0.6)"><path d="M20 7h-3.3L15 4H9L7.3 7H4a2 2 0 00-2 2v11a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2zm-8 11a4 4 0 110-8 4 4 0 010 8z"></path></svg>
              </div>
            </div>
          </div>
          <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:16px 0 20px;position:relative;">
            <div style="width:130px;height:130px;border-radius:50%;border:3px solid rgba(0,212,193,0.25);display:flex;align-items:center;justify-content:center;position:relative;animation:streak-pulse 3s ease-in-out infinite;">
              <svg width="136" height="136" style="position:absolute;top:-3px;left:-3px;transform:rotate(-90deg);" viewBox="0 0 136 136">
                <circle cx="68" cy="68" r="65" fill="none" stroke="rgba(0,212,193,0.6)" stroke-width="3" stroke-dasharray="283 127" stroke-linecap="round"></circle>
              </svg>
              <div style="display:flex;flex-direction:column;align-items:center;gap:0;">
                <svg width="36" height="44" viewBox="0 0 36 44" fill="none">
                  <path d="M18 2C18 2 28 12 28 22C28 29.7 23.7 35 18 35C12.3 35 8 29.7 8 22C8 12 18 2 18 2Z" fill="url(#flameGrad)" opacity="0.9"></path>
                  <path d="M18 14C18 14 24 20 24 25C24 28.3 21.3 31 18 31C14.7 31 12 28.3 12 25C12 20 18 14 18 14Z" fill="url(#flameInner)"></path>
                  <defs>
                    <linearGradient id="flameGrad" x1="18" y1="2" x2="18" y2="35" gradientUnits="userSpaceOnUse">
                      <stop offset="0%" stop-color="#00e5d4"></stop>
                      <stop offset="100%" stop-color="#00a896"></stop>
                    </linearGradient>
                    <linearGradient id="flameInner" x1="18" y1="14" x2="18" y2="31" gradientUnits="userSpaceOnUse">
                      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.8"></stop>
                      <stop offset="100%" stop-color="#00d4c1" stop-opacity="0.4"></stop>
                    </linearGradient>
                  </defs>
                </svg>
                <div style="font-family:'Space Grotesk',sans-serif;font-size:28px;font-weight:800;color:#fff;line-height:1;margin-top:2px;">7</div>
                <div style="font-size:10px;font-weight:600;color:rgba(0,212,193,0.8);letter-spacing:1.5px;text-transform:uppercase;margin-top:2px;">STREAK</div>
              </div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:0 12px 16px;">
            <div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:14px;text-align:center;">
              <div style="font-family:'Space Grotesk',sans-serif;font-size:24px;font-weight:800;color:#00d4c1;line-height:1;">12</div>
              <div style="font-size:10px;font-weight:600;color:rgba(255,255,255,0.4);letter-spacing:1.2px;text-transform:uppercase;margin-top:4px;">BADGES</div>
            </div>
            <div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:14px;text-align:center;">
              <div style="font-family:'Space Grotesk',sans-serif;font-size:24px;font-weight:800;color:#c084fc;line-height:1;">5</div>
              <div style="font-size:10px;font-weight:600;color:rgba(255,255,255,0.4);letter-spacing:1.2px;text-transform:uppercase;margin-top:4px;">EVENTS</div>
            </div>
          </div>
          <div style="background:rgba(255,255,255,0.05);border-top:1px solid rgba(255,255,255,0.06);display:flex;justify-content:space-around;padding:10px 0 18px;">
            <div style="display:flex;flex-direction:column;align-items:center;gap:3px;background:rgba(0,212,193,0.15);border-radius:12px;padding:6px 14px;">
              <svg width="18" height="18" fill="none" viewBox="0 0 24 24"><path d="M3 12L12 3l9 9" stroke="#00d4c1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path><path d="M5 10v9a1 1 0 001 1h4v-5h4v5h4a1 1 0 001-1v-9" stroke="#00d4c1" stroke-width="2" stroke-linecap="round"></path></svg>
              <span style="font-size:9px;color:#00d4c1;font-weight:700;">Home</span>
            </div>
            <div style="display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 10px;">
              <svg width="18" height="18" fill="none" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1" stroke="rgba(255,255,255,0.35)" stroke-width="2"></rect><rect x="14" y="3" width="7" height="7" rx="1" stroke="rgba(255,255,255,0.35)" stroke-width="2"></rect><rect x="3" y="14" width="7" height="7" rx="1" stroke="rgba(255,255,255,0.35)" stroke-width="2"></rect><rect x="14" y="14" width="7" height="7" rx="1" stroke="rgba(255,255,255,0.35)" stroke-width="2"></rect></svg>
              <span style="font-size:9px;color:rgba(255,255,255,0.35);">Scan</span>
            </div>
            <div style="display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 10px;">
              <svg width="18" height="18" fill="none" viewBox="0 0 24 24"><path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6L12 2z" stroke="rgba(255,255,255,0.35)" stroke-width="2"></path></svg>
              <span style="font-size:9px;color:rgba(255,255,255,0.35);">Badges</span>
            </div>
            <div style="display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 10px;">
              <svg width="18" height="18" fill="none" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="3" stroke="rgba(255,255,255,0.35)" stroke-width="2"></rect><path d="M16 2v4M8 2v4M3 10h18" stroke="rgba(255,255,255,0.35)" stroke-width="2" stroke-linecap="round"></path></svg>
              <span style="font-size:9px;color:rgba(255,255,255,0.35);">Events</span>
            </div>
            <div style="display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 10px;">
              <svg width="18" height="18" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4" stroke="rgba(255,255,255,0.35)" stroke-width="2"></circle><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" stroke="rgba(255,255,255,0.35)" stroke-width="2" stroke-linecap="round"></path></svg>
              <span style="font-size:9px;color:rgba(255,255,255,0.35);">Profile</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Phone 2: Events screen (center, main) ── -->
    <div :style="`animation:float-c 5s 1s ease-in-out infinite;filter:drop-shadow(0 0 48px rgba(0,212,193,0.5)) drop-shadow(0 40px 56px rgba(0,0,0,0.9));z-index:2;${single ? '' : 'margin-bottom:40px;'}`">
      <div style="width:272px;border-radius:46px;background:#0e1020;border:2.5px solid rgba(0,212,193,0.5);overflow:hidden;position:relative;">
        <div style="position:absolute;top:0;left:50%;transform:translateX(-50%);width:110px;height:30px;background:#090b13;border-radius:0 0 22px 22px;z-index:10;display:flex;align-items:center;justify-content:center;gap:6px;">
          <div style="width:9px;height:9px;border-radius:50%;background:#181a28;"></div>
          <div style="width:50px;height:8px;border-radius:4px;background:#181a28;"></div>
        </div>
        <div style="padding:38px 0 0;background:radial-gradient(ellipse at 50% 0%, #1a1530 0%, #0d0f1c 60%);min-height:540px;">
          <div style="display:flex;justify-content:space-between;padding:4px 20px 12px;font-size:10px;color:rgba(255,255,255,0.4);">
            <span>9:41</span>
            <div style="display:flex;gap:4px;align-items:center;">
              <svg width="12" height="10" viewBox="0 0 12 10"><rect x="0" y="4" width="2" height="6" fill="rgba(255,255,255,0.5)" rx="1"></rect><rect x="3" y="2" width="2" height="8" fill="rgba(255,255,255,0.5)" rx="1"></rect><rect x="6" y="0" width="2" height="10" fill="rgba(255,255,255,0.7)" rx="1"></rect><rect x="9" y="0" width="2" height="10" fill="rgba(255,255,255,0.7)" rx="1"></rect></svg>
              <svg width="14" height="10" viewBox="0 0 14 10"><rect x="0.5" y="0.5" width="11" height="9" rx="2" stroke="rgba(255,255,255,0.4)" stroke-width="1" fill="none"></rect><rect x="12" y="3" width="2" height="4" rx="1" fill="rgba(255,255,255,0.4)"></rect><rect x="1.5" y="1.5" width="7" height="7" rx="1.5" fill="rgba(255,255,255,0.7)"></rect></svg>
            </div>
          </div>
          <div style="padding:0 18px 16px;">
            <div style="font-family:'Space Grotesk',sans-serif;font-size:26px;font-weight:800;color:#fff;">Events</div>
          </div>
          <div style="display:flex;gap:8px;padding:0 18px 14px;">
            <div style="background:#22d3ee;border-radius:100px;padding:6px 16px;font-size:12px;font-weight:700;color:#0d0f1c;">All</div>
            <div style="background:rgba(255,255,255,0.07);border-radius:100px;padding:6px 14px;font-size:12px;color:rgba(255,255,255,0.5);">Active</div>
            <div style="background:rgba(255,255,255,0.07);border-radius:100px;padding:6px 14px;font-size:12px;color:rgba(255,255,255,0.5);">Past</div>
          </div>
          <div style="display:flex;align-items:center;gap:8px;padding:0 18px 16px;">
            <div style="width:32px;height:18px;border-radius:9px;background:rgba(255,255,255,0.12);position:relative;flex-shrink:0;">
              <div style="width:14px;height:14px;border-radius:50%;background:rgba(255,255,255,0.4);position:absolute;top:2px;left:2px;"></div>
            </div>
            <span style="font-size:12px;color:rgba(255,255,255,0.45);">Show past</span>
          </div>
          <div style="padding:0 18px 10px;">
            <span style="font-size:10px;font-weight:700;color:rgba(255,255,255,0.3);letter-spacing:1.5px;text-transform:uppercase;">LYFTER</span>
          </div>
          <div style="margin:0 12px 10px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);border-radius:14px;overflow:hidden;position:relative;">
            <div style="position:absolute;left:0;top:0;bottom:0;width:3px;background:#e74c3c;border-radius:3px 0 0 3px;"></div>
            <div style="padding:12px 12px 12px 16px;">
              <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:6px;">
                <div style="display:flex;align-items:center;gap:8px;">
                  <div style="width:28px;height:28px;border-radius:8px;background:linear-gradient(135deg,#00d4c1,#0097a7);display:flex;align-items:center;justify-content:center;font-size:14px;">🚀</div>
                  <div style="font-family:'Space Grotesk',sans-serif;font-size:14px;font-weight:700;color:#fff;">Spring Hackathon</div>
                </div>
                <div style="background:rgba(39,174,96,0.2);border:1px solid rgba(39,174,96,0.4);border-radius:100px;padding:2px 8px;">
                  <span style="font-size:10px;font-weight:600;color:#27ae60;">Active</span>
                </div>
              </div>
              <div style="display:flex;align-items:center;gap:5px;margin-bottom:10px;">
                <svg width="11" height="11" fill="none" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="3" stroke="rgba(255,255,255,0.35)" stroke-width="2"></rect><path d="M16 2v4M8 2v4M3 10h18" stroke="rgba(255,255,255,0.35)" stroke-width="2" stroke-linecap="round"></path></svg>
                <span style="font-size:11px;color:rgba(255,255,255,0.35);">Today · 7:00 PM</span>
              </div>
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                <span style="font-size:11px;color:rgba(255,255,255,0.4);">Progress</span>
                <span style="font-size:11px;color:rgba(255,255,255,0.4);">3 of 5 badges</span>
              </div>
              <div style="height:3px;background:rgba(255,255,255,0.08);border-radius:2px;overflow:hidden;">
                <div style="height:100%;width:60%;background:linear-gradient(90deg,#00d4c1,#22d3ee);border-radius:2px;"></div>
              </div>
            </div>
          </div>
          <div style="margin:0 12px 10px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);border-radius:14px;overflow:hidden;position:relative;">
            <div style="position:absolute;left:0;top:0;bottom:0;width:3px;background:#e74c3c;border-radius:3px 0 0 3px;"></div>
            <div style="padding:12px 12px 12px 16px;">
              <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:6px;">
                <div style="display:flex;align-items:center;gap:8px;">
                  <div style="width:28px;height:28px;border-radius:8px;background:linear-gradient(135deg,#c084fc,#7c3aed);display:flex;align-items:center;justify-content:center;font-size:14px;">🎤</div>
                  <div style="font-family:'Space Grotesk',sans-serif;font-size:14px;font-weight:700;color:#fff;">Leadership Talk</div>
                </div>
                <div style="background:rgba(39,174,96,0.2);border:1px solid rgba(39,174,96,0.4);border-radius:100px;padding:2px 8px;">
                  <span style="font-size:10px;font-weight:600;color:#27ae60;">Active</span>
                </div>
              </div>
              <div style="display:flex;align-items:center;gap:5px;margin-bottom:10px;">
                <svg width="11" height="11" fill="none" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="3" stroke="rgba(255,255,255,0.35)" stroke-width="2"></rect><path d="M16 2v4M8 2v4M3 10h18" stroke="rgba(255,255,255,0.35)" stroke-width="2" stroke-linecap="round"></path></svg>
                <span style="font-size:11px;color:rgba(255,255,255,0.35);">Thu · 2:00 PM</span>
              </div>
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                <span style="font-size:11px;color:rgba(255,255,255,0.4);">Progress</span>
                <span style="font-size:11px;color:rgba(255,255,255,0.4);">1 of 4 badges</span>
              </div>
              <div style="height:3px;background:rgba(255,255,255,0.08);border-radius:2px;overflow:hidden;">
                <div style="height:100%;width:25%;background:linear-gradient(90deg,#c084fc,#a855f7);border-radius:2px;"></div>
              </div>
            </div>
          </div>
          <div style="text-align:center;padding:8px 0 12px;">
            <span style="font-size:18px;font-weight:800;color:rgba(255,255,255,0.06);font-family:'Space Grotesk',sans-serif;">01</span>
          </div>
          <div style="background:rgba(255,255,255,0.05);border-top:1px solid rgba(255,255,255,0.06);display:flex;justify-content:space-around;padding:10px 0 20px;">
            <div style="display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 10px;">
              <svg width="18" height="18" fill="none" viewBox="0 0 24 24"><path d="M3 12L12 3l9 9" stroke="rgba(255,255,255,0.35)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path><path d="M5 10v9a1 1 0 001 1h4v-5h4v5h4a1 1 0 001-1v-9" stroke="rgba(255,255,255,0.35)" stroke-width="2" stroke-linecap="round"></path></svg>
              <span style="font-size:9px;color:rgba(255,255,255,0.35);">Home</span>
            </div>
            <div style="display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 10px;">
              <svg width="18" height="18" fill="none" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1" stroke="rgba(255,255,255,0.35)" stroke-width="2"></rect><rect x="14" y="3" width="7" height="7" rx="1" stroke="rgba(255,255,255,0.35)" stroke-width="2"></rect><rect x="3" y="14" width="7" height="7" rx="1" stroke="rgba(255,255,255,0.35)" stroke-width="2"></rect><rect x="14" y="14" width="7" height="7" rx="1" stroke="rgba(255,255,255,0.35)" stroke-width="2"></rect></svg>
              <span style="font-size:9px;color:rgba(255,255,255,0.35);">Scan</span>
            </div>
            <div style="display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 10px;">
              <svg width="18" height="18" fill="none" viewBox="0 0 24 24"><path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6L12 2z" stroke="rgba(255,255,255,0.35)" stroke-width="2"></path></svg>
              <span style="font-size:9px;color:rgba(255,255,255,0.35);">Badges</span>
            </div>
            <div style="display:flex;flex-direction:column;align-items:center;gap:3px;background:rgba(0,212,193,0.15);border-radius:12px;padding:6px 12px;">
              <svg width="18" height="18" fill="none" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="3" stroke="#00d4c1" stroke-width="2"></rect><path d="M16 2v4M8 2v4M3 10h18" stroke="#00d4c1" stroke-width="2" stroke-linecap="round"></path></svg>
              <span style="font-size:9px;color:#00d4c1;font-weight:700;">Events</span>
            </div>
            <div style="display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 10px;">
              <svg width="18" height="18" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4" stroke="rgba(255,255,255,0.35)" stroke-width="2"></circle><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" stroke="rgba(255,255,255,0.35)" stroke-width="2" stroke-linecap="round"></path></svg>
              <span style="font-size:9px;color:rgba(255,255,255,0.35);">Profile</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Phone 3: Scan / QR ── (hidden in single mode and on narrow screens) -->
    <div v-if="!single" class="ap-side" style="animation:float-b 7s 2s ease-in-out infinite;filter:drop-shadow(0 0 36px rgba(192,132,252,0.4)) drop-shadow(0 32px 48px rgba(0,0,0,0.9));">
      <div style="width:258px;border-radius:44px;background:#0e1020;border:2px solid rgba(192,132,252,0.4);overflow:hidden;position:relative;">
        <div style="position:absolute;top:0;left:50%;transform:translateX(-50%);width:100px;height:28px;background:#090b13;border-radius:0 0 20px 20px;z-index:10;display:flex;align-items:center;justify-content:center;gap:6px;">
          <div style="width:8px;height:8px;border-radius:50%;background:#181a28;"></div>
          <div style="width:46px;height:8px;border-radius:4px;background:#181a28;"></div>
        </div>
        <div style="padding:36px 0 0;background:radial-gradient(ellipse at 50% 20%, #1a1535 0%, #0d0f1c 70%);min-height:480px;">
          <div style="display:flex;justify-content:space-between;padding:4px 18px 10px;font-size:10px;color:rgba(255,255,255,0.4);">
            <span>9:41</span>
            <div style="display:flex;gap:4px;align-items:center;">
              <svg width="12" height="10" viewBox="0 0 12 10"><rect x="0" y="4" width="2" height="6" fill="rgba(255,255,255,0.5)" rx="1"></rect><rect x="3" y="2" width="2" height="8" fill="rgba(255,255,255,0.5)" rx="1"></rect><rect x="6" y="0" width="2" height="10" fill="rgba(255,255,255,0.7)" rx="1"></rect><rect x="9" y="0" width="2" height="10" fill="rgba(255,255,255,0.7)" rx="1"></rect></svg>
            </div>
          </div>
          <div style="padding:0 18px 16px;">
            <div style="font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:800;color:#fff;">Scan Badge</div>
            <div style="font-size:12px;color:rgba(255,255,255,0.4);margin-top:2px;">Spring Hackathon 2025</div>
          </div>
          <div style="margin:0 14px 16px;border-radius:18px;background:#06080f;overflow:hidden;position:relative;height:200px;display:flex;align-items:center;justify-content:center;">
            <svg width="140" height="140" viewBox="0 0 140 140" fill="none" style="opacity:0.9;">
              <rect x="10" y="10" width="40" height="40" rx="4" fill="none" stroke="#c084fc" stroke-width="4"></rect>
              <rect x="20" y="20" width="20" height="20" rx="2" fill="#c084fc"></rect>
              <rect x="90" y="10" width="40" height="40" rx="4" fill="none" stroke="#c084fc" stroke-width="4"></rect>
              <rect x="100" y="20" width="20" height="20" rx="2" fill="#c084fc"></rect>
              <rect x="10" y="90" width="40" height="40" rx="4" fill="none" stroke="#c084fc" stroke-width="4"></rect>
              <rect x="20" y="100" width="20" height="20" rx="2" fill="#c084fc"></rect>
              <rect x="60" y="10" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="75" y="10" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="60" y="25" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="75" y="25" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="10" y="60" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="25" y="60" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="10" y="75" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="60" y="60" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="75" y="60" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="90" y="60" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="105" y="60" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="120" y="60" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="60" y="75" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="90" y="75" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="120" y="75" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="60" y="90" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="75" y="90" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="105" y="90" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="60" y="105" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="90" y="105" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="120" y="105" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="60" y="120" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="75" y="120" width="10" height="10" rx="1" fill="#c084fc"></rect>
              <rect x="105" y="120" width="10" height="10" rx="1" fill="#c084fc"></rect>
            </svg>
            <div style="position:absolute;left:20px;right:20px;height:2px;background:linear-gradient(90deg,transparent,#c084fc,transparent);animation:scan-line 2s ease-in-out infinite alternate;border-radius:1px;"></div>
            <div style="position:absolute;top:12px;left:12px;width:22px;height:22px;border-top:2.5px solid #c084fc;border-left:2.5px solid #c084fc;border-radius:4px 0 0 0;"></div>
            <div style="position:absolute;top:12px;right:12px;width:22px;height:22px;border-top:2.5px solid #c084fc;border-right:2.5px solid #c084fc;border-radius:0 4px 0 0;"></div>
            <div style="position:absolute;bottom:12px;left:12px;width:22px;height:22px;border-bottom:2.5px solid #c084fc;border-left:2.5px solid #c084fc;border-radius:0 0 0 4px;"></div>
            <div style="position:absolute;bottom:12px;right:12px;width:22px;height:22px;border-bottom:2.5px solid #c084fc;border-right:2.5px solid #c084fc;border-radius:0 0 4px 0;"></div>
          </div>
          <div style="margin:0 14px 12px;background:rgba(0,212,193,0.1);border:1px solid rgba(0,212,193,0.25);border-radius:12px;padding:10px 14px;display:flex;align-items:center;gap:10px;">
            <div style="width:8px;height:8px;border-radius:50%;background:#00d4c1;animation:blink 1.4s ease-in-out infinite;flex-shrink:0;"></div>
            <div>
              <div style="font-size:12px;font-weight:600;color:#00d4c1;">Badge Redeemed ✓</div>
              <div style="font-size:10px;color:rgba(255,255,255,0.4);margin-top:1px;">+150 pts · Spring Hackathon</div>
            </div>
          </div>
          <div style="background:rgba(255,255,255,0.05);border-top:1px solid rgba(255,255,255,0.06);display:flex;justify-content:space-around;padding:10px 0 18px;">
            <div style="display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 10px;">
              <svg width="18" height="18" fill="none" viewBox="0 0 24 24"><path d="M3 12L12 3l9 9" stroke="rgba(255,255,255,0.35)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path><path d="M5 10v9a1 1 0 001 1h4v-5h4v5h4a1 1 0 001-1v-9" stroke="rgba(255,255,255,0.35)" stroke-width="2" stroke-linecap="round"></path></svg>
              <span style="font-size:9px;color:rgba(255,255,255,0.35);">Home</span>
            </div>
            <div style="display:flex;flex-direction:column;align-items:center;gap:3px;background:rgba(192,132,252,0.15);border-radius:12px;padding:6px 12px;">
              <svg width="18" height="18" fill="none" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1" stroke="#c084fc" stroke-width="2"></rect><rect x="14" y="3" width="7" height="7" rx="1" stroke="#c084fc" stroke-width="2"></rect><rect x="3" y="14" width="7" height="7" rx="1" stroke="#c084fc" stroke-width="2"></rect><rect x="14" y="14" width="7" height="7" rx="1" stroke="#c084fc" stroke-width="2"></rect></svg>
              <span style="font-size:9px;color:#c084fc;font-weight:700;">Scan</span>
            </div>
            <div style="display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 10px;">
              <svg width="18" height="18" fill="none" viewBox="0 0 24 24"><path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6L12 2z" stroke="rgba(255,255,255,0.35)" stroke-width="2"></path></svg>
              <span style="font-size:9px;color:rgba(255,255,255,0.35);">Badges</span>
            </div>
            <div style="display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 10px;">
              <svg width="18" height="18" fill="none" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="3" stroke="rgba(255,255,255,0.35)" stroke-width="2"></rect><path d="M16 2v4M8 2v4M3 10h18" stroke="rgba(255,255,255,0.35)" stroke-width="2" stroke-linecap="round"></path></svg>
              <span style="font-size:9px;color:rgba(255,255,255,0.35);">Events</span>
            </div>
            <div style="display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px 10px;">
              <svg width="18" height="18" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4" stroke="rgba(255,255,255,0.35)" stroke-width="2"></circle><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" stroke="rgba(255,255,255,0.35)" stroke-width="2" stroke-linecap="round"></path></svg>
              <span style="font-size:9px;color:rgba(255,255,255,0.35);">Profile</span>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<style>
/* On phones the three-phone row overflows; show just the centre phone. */
@media (max-width: 680px) {
  .app-preview { gap: 0 !important; }
  .app-preview .ap-side { display: none !important; }
}
</style>
