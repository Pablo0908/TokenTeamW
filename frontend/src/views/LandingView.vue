<script setup>
// Public marketing preview shown to logged-out visitors. The real sign-in form
// (LoginView, with all its credential/OTP/Google logic) is embedded at the bottom,
// so visitors see the preview first and scroll down to sign in. Preview buttons
// scroll to that auth section (or the features section) rather than dead-ending.
import { ref } from 'vue'
import logo from '@/assets/lyfter-logo.png'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import AppPreview from '@/components/ui/AppPreview.vue'

// The auth panel at the bottom toggles between sign-up and log-in. Visitors reach it
// by scrolling past the entire preview; CTAs jump straight to the right tab.
const authMode = ref('register') // 'register' | 'login'

function scrollTo(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
function goAuth(mode) {
  authMode.value = mode
  scrollTo('landing-auth')
}
</script>

<template>
<div class="landing">

<!-- ─── NAV ─────────────────────────────────────────────────────────────── -->
<nav class="lp-nav" style="position:fixed;top:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:0 48px;height:64px;background:rgba(9,11,19,0.9);backdrop-filter:blur(16px);border-bottom:1px solid rgba(0,212,193,0.3);box-shadow:0 1px 12px rgba(0,212,193,0.12);">
  <div style="display:flex;align-items:center;gap:10px;">
    <img :src="logo" width="36" height="36" style="border-radius:10px;display:block;" alt="Lyfter Badges" />
    <span style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:18px;letter-spacing:-0.3px;color:#fff;">Lyfter Badges</span>
  </div>
  <div class="lp-nav-links" style="display:flex;align-items:center;gap:32px;">
    <a @click="scrollTo('landing-features')" class="lp-link" style="color:rgba(232,234,240,0.6);font-size:14px;font-weight:500;text-decoration:none;cursor:pointer;transition:all 0.2s ease;">Features</a>
  </div>
  <div class="lp-nav-cta" style="display:flex;align-items:center;gap:12px;">
    <button @click="goAuth('login')" class="lp-btn-ghost" style="background:transparent;border:1px solid rgba(255,255,255,0.15);color:#e8eaf0;font-family:'DM Sans',sans-serif;font-size:14px;font-weight:500;padding:8px 20px;border-radius:8px;cursor:pointer;transition:all 0.2s ease;">Log in</button>
    <button @click="goAuth('register')" class="lp-btn-primary" style="background:linear-gradient(135deg,#00d4c1,#0097a7);border:none;color:#fff;font-family:'DM Sans',sans-serif;font-size:14px;font-weight:600;padding:8px 20px;border-radius:8px;cursor:pointer;transition:all 0.2s ease;">Get started</button>
  </div>
</nav>

<!-- ─── HERO ───────────────────────────────────────────────────────────── -->
<section class="lp-hero" style="min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:120px 40px 80px;position:relative;overflow:hidden;">

  <!-- background orbs -->
  <div style="position:absolute;top:-100px;left:-140px;width:600px;height:600px;border-radius:50%;background:radial-gradient(circle,rgba(0,212,193,0.15) 0%,transparent 70%);animation:pulse-orb 8s ease-in-out infinite;pointer-events:none;will-change:transform;"></div>
  <div style="position:absolute;bottom:-60px;right:-80px;width:480px;height:480px;border-radius:50%;background:radial-gradient(circle,rgba(168,85,247,0.12) 0%,transparent 70%);animation:pulse-orb 10s 2s ease-in-out infinite;pointer-events:none;will-change:transform;"></div>
  <div style="position:absolute;top:40%;left:38%;width:280px;height:280px;border-radius:50%;background:radial-gradient(circle,rgba(0,212,193,0.08) 0%,transparent 70%);animation:pulse-orb 12s 4s ease-in-out infinite;pointer-events:none;will-change:transform;"></div>

  <!-- grid -->
  <div style="position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,0.02) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.02) 1px,transparent 1px);background-size:64px 64px;pointer-events:none;mask-image:radial-gradient(ellipse 80% 80% at 50% 50%,black 40%,transparent 100%);"></div>

  <!-- headline -->
  <h1 style="font-family:'Space Grotesk',sans-serif;font-size:clamp(44px,6vw,80px);font-weight:800;line-height:1.05;letter-spacing:-2px;text-align:center;max-width:860px;margin-bottom:24px;text-wrap:balance;">
    Gana badges.<br />
    <span class="lp-gradient-text" style="background:linear-gradient(90deg,#00d4c1,#22d3ee,#a78bfa,#00d4c1);background-size:200% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;animation:lp-gradient-shift 4s linear infinite;">Asiste a eventos.</span><br />
    Recibe recompensas.
  </h1>

  <p class="lp-sub" style="font-size:18px;font-weight:400;color:rgba(232,234,240,0.55);text-align:center;max-width:520px;line-height:1.65;margin-bottom:40px;text-wrap:pretty;">
    La plataforma todo en uno para que tu organizacion realice eventos, emita badges verificables y recompense a sus miembros, directo desde el celular.
  </p>

  <div class="lp-btn-row" style="display:flex;align-items:center;gap:14px;margin-bottom:80px;">
    <button @click="goAuth('register')" class="lp-btn-primary" style="background:linear-gradient(135deg,#00d4c1,#0097a7);border:none;color:#fff;font-family:'DM Sans',sans-serif;font-size:15px;font-weight:600;padding:14px 32px;border-radius:10px;cursor:pointer;box-shadow:0 8px 32px rgba(0,212,193,0.35);transition:all 0.2s ease;">Empieza gratis</button>
    <button @click="scrollTo('landing-features')" class="lp-btn-ghost" style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);color:#e8eaf0;font-family:'DM Sans',sans-serif;font-size:15px;font-weight:500;padding:14px 32px;border-radius:10px;cursor:pointer;transition:all 0.2s ease;">Ver funciones</button>
  </div>

  <!-- App phone mockups -->
  <AppPreview />
</section>

<!-- ─── SOCIAL PROOF TICKER ───────────────────────────────────────────── -->
<div class="lp-ticker-wrap" style="padding:0 40px 80px;overflow:hidden;position:relative;">
  <p style="text-align:center;font-size:13px;color:rgba(255,255,255,0.25);letter-spacing:1px;text-transform:uppercase;margin-bottom:28px;">Hecho para comunidades que crecen</p>
  <div class="lp-ticker" style="display:flex;justify-content:center;flex-wrap:wrap;gap:16px;max-width:1100px;margin:0 auto;">
    <div class="lp-chip" style="opacity:0;animation:lp-chip-in 0.6s ease forwards;animation-delay:0.05s;display:inline-flex;align-items:center;gap:8px;background:rgba(0,212,193,0.06);border:1px solid rgba(0,212,193,0.22);border-radius:100px;padding:12px 22px;backdrop-filter:blur(8px);box-shadow:0 0 24px rgba(0,212,193,0.12);">
      <span style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:800;color:#00d4c1;">500+</span>
      <span style="font-size:14px;color:rgba(255,255,255,0.6);">eventos creados</span>
    </div>
    <div class="lp-chip" style="opacity:0;animation:lp-chip-in 0.6s ease forwards;animation-delay:0.18s;display:inline-flex;align-items:center;gap:8px;background:rgba(0,212,193,0.06);border:1px solid rgba(0,212,193,0.22);border-radius:100px;padding:12px 22px;backdrop-filter:blur(8px);box-shadow:0 0 24px rgba(0,212,193,0.12);">
      <span style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:800;color:#00d4c1;">12,000+</span>
      <span style="font-size:14px;color:rgba(255,255,255,0.6);">badges emitidos</span>
    </div>
    <div class="lp-chip" style="opacity:0;animation:lp-chip-in 0.6s ease forwards;animation-delay:0.31s;display:inline-flex;align-items:center;gap:8px;background:rgba(0,212,193,0.06);border:1px solid rgba(0,212,193,0.22);border-radius:100px;padding:12px 22px;backdrop-filter:blur(8px);box-shadow:0 0 24px rgba(0,212,193,0.12);">
      <span style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:800;color:#00d4c1;">98%</span>
      <span style="font-size:14px;color:rgba(255,255,255,0.6);">tasa de escaneo</span>
    </div>
    <div class="lp-chip" style="opacity:0;animation:lp-chip-in 0.6s ease forwards;animation-delay:0.44s;display:inline-flex;align-items:center;gap:8px;background:rgba(0,212,193,0.06);border:1px solid rgba(0,212,193,0.22);border-radius:100px;padding:12px 22px;backdrop-filter:blur(8px);box-shadow:0 0 24px rgba(0,212,193,0.12);">
      <span style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:800;color:#00d4c1;">40+</span>
      <span style="font-size:14px;color:rgba(255,255,255,0.6);">organizaciones</span>
    </div>
  </div>
</div>

<!-- ─── FEATURES GRID ─────────────────────────────────────────────────── -->
<section id="landing-features" class="lp-features" style="padding:0 40px 100px;max-width:1200px;margin:0 auto;">
  <div style="text-align:center;margin-bottom:56px;">
    <p style="font-size:13px;color:#00d4c1;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:12px;">Todo en una sola app</p>
    <h2 style="font-family:'Space Grotesk',sans-serif;font-size:clamp(32px,4vw,52px);font-weight:800;color:#fff;letter-spacing:-1.5px;">Pensado para toda tu comunidad</h2>
  </div>
  <div class="lp-features-grid" style="display:grid;grid-template-columns:repeat(3,1fr);gap:20px;">
    <div class="lp-card" style="background:linear-gradient(145deg,rgba(0,212,193,0.08),rgba(0,212,193,0.02));border:1px solid rgba(0,212,193,0.15);border-radius:20px;padding:28px;transition:all 0.2s ease;">
      <div style="width:44px;height:44px;border-radius:12px;background:rgba(0,212,193,0.15);border:1px solid rgba(0,212,193,0.25);display:flex;align-items:center;justify-content:center;margin-bottom:18px;">
        <svg width="22" height="22" fill="none" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="3" stroke="#00d4c1" stroke-width="2"></rect><path d="M16 2v4M8 2v4M3 10h18" stroke="#00d4c1" stroke-width="2" stroke-linecap="round"></path></svg>
      </div>
      <h3 style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:700;color:#fff;margin-bottom:10px;">Gestion de eventos</h3>
      <p style="font-size:14px;color:rgba(255,255,255,0.5);line-height:1.65;">Crea eventos y controla la asistencia desde el panel de administracion.</p>
    </div>
    <div class="lp-card" style="background:linear-gradient(145deg,rgba(192,132,252,0.1),rgba(192,132,252,0.03));border:1px solid rgba(192,132,252,0.18);border-radius:20px;padding:28px;transition:all 0.2s ease;">
      <div style="width:44px;height:44px;border-radius:12px;background:rgba(192,132,252,0.15);border:1px solid rgba(192,132,252,0.25);display:flex;align-items:center;justify-content:center;margin-bottom:18px;">
        <svg width="22" height="22" fill="none" viewBox="0 0 24 24"><path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6L12 2z" stroke="#c084fc" stroke-width="2"></path></svg>
      </div>
      <h3 style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:700;color:#fff;margin-bottom:10px;">Billetera de badges</h3>
      <p style="font-size:14px;color:rgba(255,255,255,0.5);line-height:1.65;">Los miembros coleccionan badges verificables por cada evento al que asisten.</p>
    </div>
    <div class="lp-card" style="background:linear-gradient(145deg,rgba(231,76,60,0.08),rgba(231,76,60,0.02));border:1px solid rgba(231,76,60,0.15);border-radius:20px;padding:28px;transition:all 0.2s ease;">
      <div style="width:44px;height:44px;border-radius:12px;background:rgba(231,76,60,0.12);border:1px solid rgba(231,76,60,0.25);display:flex;align-items:center;justify-content:center;margin-bottom:18px;">
        <svg width="22" height="22" fill="none" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1" stroke="#e74c3c" stroke-width="2"></rect><rect x="14" y="3" width="7" height="7" rx="1" stroke="#e74c3c" stroke-width="2"></rect><rect x="3" y="14" width="7" height="7" rx="1" stroke="#e74c3c" stroke-width="2"></rect><path d="M14 17h7M17 14v7" stroke="#e74c3c" stroke-width="2" stroke-linecap="round"></path></svg>
      </div>
      <h3 style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:700;color:#fff;margin-bottom:10px;">Canje por QR</h3>
      <p style="font-size:14px;color:rgba(255,255,255,0.5);line-height:1.65;">Escanea para ganar con sincronizacion offline, funciona incluso sin conexion.</p>
    </div>
    <div class="lp-card" style="background:linear-gradient(145deg,rgba(245,166,35,0.08),rgba(245,166,35,0.02));border:1px solid rgba(245,166,35,0.15);border-radius:20px;padding:28px;transition:all 0.2s ease;">
      <div style="width:44px;height:44px;border-radius:12px;background:rgba(245,166,35,0.12);border:1px solid rgba(245,166,35,0.25);display:flex;align-items:center;justify-content:center;margin-bottom:18px;">
        <svg width="22" height="22" fill="none" viewBox="0 0 24 24"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" stroke="#f5a623" stroke-width="2" stroke-linejoin="round"></path><path d="M13.73 21a2 2 0 01-3.46 0" stroke="#f5a623" stroke-width="2" stroke-linecap="round"></path></svg>
      </div>
      <h3 style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:700;color:#fff;margin-bottom:10px;">Anuncios</h3>
      <p style="font-size:14px;color:rgba(255,255,255,0.5);line-height:1.65;">Envia anuncios a todos los miembros al instante.</p>
    </div>
    <div class="lp-card" style="background:linear-gradient(145deg,rgba(59,130,246,0.08),rgba(59,130,246,0.02));border:1px solid rgba(59,130,246,0.15);border-radius:20px;padding:28px;transition:all 0.2s ease;">
      <div style="width:44px;height:44px;border-radius:12px;background:rgba(59,130,246,0.12);border:1px solid rgba(59,130,246,0.25);display:flex;align-items:center;justify-content:center;margin-bottom:18px;">
        <svg width="22" height="22" fill="none" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="#60a5fa" stroke-width="2" stroke-linejoin="round"></path></svg>
      </div>
      <h3 style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:700;color:#fff;margin-bottom:10px;">Multi-organizacion y roles</h3>
      <p style="font-size:14px;color:rgba(255,255,255,0.5);line-height:1.65;">Autenticacion OTP, flujos de invitacion y accesos por rol para cada organizacion.</p>
    </div>
    <div class="lp-card" style="background:linear-gradient(145deg,rgba(251,146,60,0.1),rgba(251,146,60,0.03));border:1px solid rgba(251,146,60,0.18);border-radius:20px;padding:28px;transition:all 0.2s ease;">
      <div style="width:44px;height:44px;border-radius:12px;background:rgba(251,146,60,0.14);border:1px solid rgba(251,146,60,0.28);display:flex;align-items:center;justify-content:center;margin-bottom:18px;">
        <svg width="22" height="22" fill="none" viewBox="0 0 24 24"><path d="M12 2c1 3-1 5-1 7a3 3 0 006 0c1 2 2 3.5 2 6a7 7 0 11-14 0c0-3 2-5 3-7 .5 2 2 3 2.5 2.5C12 11 11 7 12 2z" stroke="#fb923c" stroke-width="2" stroke-linejoin="round"></path></svg>
      </div>
      <h3 style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:700;color:#fff;margin-bottom:10px;">Rachas de eventos</h3>
      <p style="font-size:14px;color:rgba(255,255,255,0.5);line-height:1.65;">Mantiene la motivacion con rachas que premian la asistencia continua.</p>
    </div>
  </div>
</section>

<!-- ─── HOW IT WORKS ──────────────────────────────────────────────────── -->
<section class="lp-steps" style="padding:0 40px 100px;max-width:1100px;margin:0 auto;">
  <div style="text-align:center;margin-bottom:56px;">
    <p style="font-size:13px;color:#00d4c1;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:12px;">Como funciona</p>
    <h2 style="font-family:'Space Grotesk',sans-serif;font-size:clamp(28px,4vw,44px);font-weight:800;color:#fff;letter-spacing:-1.5px;">Tres pasos y listo</h2>
  </div>
  <div class="lp-steps-row" style="display:flex;align-items:flex-start;justify-content:center;gap:24px;position:relative;">
    <!-- connecting dashed line -->
    <div class="lp-steps-line" style="position:absolute;top:28px;left:16%;right:16%;height:0;border-top:2px dashed rgba(0,212,193,0.3);pointer-events:none;"></div>

    <div class="lp-step" style="flex:1;max-width:300px;text-align:center;position:relative;z-index:1;">
      <div style="width:56px;height:56px;border-radius:50%;margin:0 auto 20px;display:flex;align-items:center;justify-content:center;background:rgba(0,212,193,0.12);border:2px solid #00d4c1;font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:800;color:#00d4c1;box-shadow:0 0 24px rgba(0,212,193,0.3);">1</div>
      <h3 style="font-family:'Space Grotesk',sans-serif;font-size:17px;font-weight:700;color:#fff;margin-bottom:8px;">Crea el evento</h3>
      <p style="font-size:14px;color:rgba(255,255,255,0.5);line-height:1.6;">El admin crea el evento y genera los QR codes.</p>
    </div>

    <div class="lp-step" style="flex:1;max-width:300px;text-align:center;position:relative;z-index:1;">
      <div style="width:56px;height:56px;border-radius:50%;margin:0 auto 20px;display:flex;align-items:center;justify-content:center;background:rgba(0,212,193,0.12);border:2px solid #00d4c1;font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:800;color:#00d4c1;box-shadow:0 0 24px rgba(0,212,193,0.3);">2</div>
      <h3 style="font-family:'Space Grotesk',sans-serif;font-size:17px;font-weight:700;color:#fff;margin-bottom:8px;">Escanea en cada estacion</h3>
      <p style="font-size:14px;color:rgba(255,255,255,0.5);line-height:1.6;">Los participantes escanean el QR en cada estacion del evento.</p>
    </div>

    <div class="lp-step" style="flex:1;max-width:300px;text-align:center;position:relative;z-index:1;">
      <div style="width:56px;height:56px;border-radius:50%;margin:0 auto 20px;display:flex;align-items:center;justify-content:center;background:rgba(0,212,193,0.12);border:2px solid #00d4c1;font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:800;color:#00d4c1;box-shadow:0 0 24px rgba(0,212,193,0.3);">3</div>
      <h3 style="font-family:'Space Grotesk',sans-serif;font-size:17px;font-weight:700;color:#fff;margin-bottom:8px;">Acumula badges y rachas</h3>
      <p style="font-size:14px;color:rgba(255,255,255,0.5);line-height:1.6;">Se acumulan badges y rachas automaticamente.</p>
    </div>
  </div>
</section>

<!-- ─── CTA ────────────────────────────────────────────────────────────── -->
<section class="lp-cta" style="padding:80px 40px 120px;text-align:center;position:relative;overflow:hidden;">
  <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:600px;height:400px;background:radial-gradient(ellipse,rgba(0,212,193,0.12) 0%,transparent 70%);pointer-events:none;"></div>
  <p style="font-size:13px;color:#00d4c1;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:16px;">Listo para empezar</p>
  <h2 style="font-family:'Space Grotesk',sans-serif;font-size:clamp(36px,5vw,64px);font-weight:800;color:#fff;letter-spacing:-2px;margin-bottom:20px;">Construye<br />tu comunidad.</h2>
  <p style="font-size:17px;color:rgba(255,255,255,0.45);margin-bottom:40px;max-width:480px;margin-left:auto;margin-right:auto;line-height:1.65;">Configura tu organizacion en minutos y deja que tus miembros escaneen badges desde el primer dia.</p>
  <div class="lp-btn-row" style="display:flex;justify-content:center;gap:14px;">
    <button @click="goAuth('register')" class="lp-btn-primary" style="background:linear-gradient(135deg,#00d4c1,#0097a7);border:none;color:#fff;font-family:'DM Sans',sans-serif;font-size:16px;font-weight:600;padding:16px 40px;border-radius:12px;cursor:pointer;box-shadow:0 12px 40px rgba(0,212,193,0.35);transition:all 0.2s ease;">Get the app</button>
    <a href="mailto:lyfterbadges@gmail.com" class="lp-btn-ghost" style="display:inline-flex;align-items:center;justify-content:center;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);color:#e8eaf0;font-family:'DM Sans',sans-serif;font-size:16px;font-weight:500;padding:16px 40px;border-radius:12px;cursor:pointer;text-decoration:none;transition:all 0.2s ease;">Hablar con ventas</a>
  </div>
</section>

<!-- ─── SIGN UP / LOG IN ───────────────────────────────────────────────── -->
<section id="landing-auth" style="border-top:1px solid rgba(255,255,255,0.06);background:rgba(255,255,255,0.02);padding:56px 0 48px;">
  <p style="text-align:center;font-size:13px;color:#00d4c1;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:20px;">Join the community</p>

  <!-- segmented Sign up / Log in toggle -->
  <div style="display:flex;justify-content:center;margin-bottom:8px;">
    <div style="display:inline-flex;gap:4px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-radius:100px;padding:4px;">
      <button
        @click="authMode = 'register'"
        :style="`border:none;cursor:pointer;border-radius:100px;padding:8px 26px;font-family:'DM Sans',sans-serif;font-size:14px;font-weight:600;transition:all .2s;${authMode === 'register' ? 'background:linear-gradient(135deg,#00d4c1,#0097a7);color:#06231f;box-shadow:0 4px 16px rgba(0,212,193,0.35);' : 'background:transparent;color:rgba(232,234,240,0.6);'}`"
      >Sign up</button>
      <button
        @click="authMode = 'login'"
        :style="`border:none;cursor:pointer;border-radius:100px;padding:8px 26px;font-family:'DM Sans',sans-serif;font-size:14px;font-weight:600;transition:all .2s;${authMode === 'login' ? 'background:linear-gradient(135deg,#00d4c1,#0097a7);color:#06231f;box-shadow:0 4px 16px rgba(0,212,193,0.35);' : 'background:transparent;color:rgba(232,234,240,0.6);'}`"
      >Log in</button>
    </div>
  </div>

  <RegisterView v-if="authMode === 'register'" :embedded="true" @switch="authMode = 'login'" />
  <LoginView v-else :embedded="true" @switch="authMode = 'register'" />
</section>

<!-- ─── FOOTER ────────────────────────────────────────────────────────── -->
<footer class="lp-footer" style="padding:32px 48px;border-top:1px solid rgba(255,255,255,0.06);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;">
  <div style="display:flex;align-items:center;gap:8px;">
    <img :src="logo" width="28" height="28" style="border-radius:8px;display:block;" alt="Lyfter Badges" />
    <span style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:15px;color:rgba(255,255,255,0.7);">Lyfter Badges</span>
  </div>
  <span style="font-size:13px;color:rgba(255,255,255,0.2);">© 2026 Lyfter Badges · Hecho con amor para comunidades que crecen.</span>
  <div style="display:flex;gap:20px;">
    <a href="#" class="lp-link" style="font-size:13px;color:rgba(255,255,255,0.3);text-decoration:none;cursor:pointer;transition:all 0.2s ease;">Terminos</a>
    <a href="#" class="lp-link" style="font-size:13px;color:rgba(255,255,255,0.3);text-decoration:none;cursor:pointer;transition:all 0.2s ease;">Privacidad</a>
  </div>
</footer>

</div>
</template>

<style>
/* Page shell only — preview keyframes live globally in style.css so they're shared
   with the auth hero (AppPreview) and honor the app's reduced-motion / fx-off settings. */
.landing {
  background: #090b13;
  color: #e8eaf0;
  font-family: 'DM Sans', sans-serif;
  min-height: 100dvh;
  overflow-x: hidden;
}

/* Keep scroll-to-section jumps clear of the fixed navbar. */
.landing #landing-features,
.landing #landing-auth { scroll-margin-top: 76px; }

/* ── Interactive hover polish ─────────────────────────────────────────── */
.landing .lp-link:hover { color: #00d4c1; }

.landing .lp-btn-primary:hover {
  transform: scale(1.03);
  box-shadow: 0 12px 44px rgba(0, 212, 193, 0.55);
}
.landing .lp-btn-ghost:hover {
  transform: scale(1.03);
  border-color: rgba(0, 212, 193, 0.4);
  background: rgba(0, 212, 193, 0.08);
}

.landing .lp-card:hover {
  transform: translateY(-4px);
  border-color: rgba(0, 212, 193, 0.45);
}

/* ── Animations ───────────────────────────────────────────────────────── */
@keyframes lp-gradient-shift {
  0% { background-position: 0% center; }
  100% { background-position: 200% center; }
}

@keyframes lp-chip-in {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Honor reduced-motion: stop the looping/auto effects and reveal chips. */
@media (prefers-reduced-motion: reduce) {
  .landing .lp-gradient-text { animation: none; }
  .landing .lp-chip { animation: none !important; opacity: 1 !important; }
}

/* ── Responsive overrides ──────────────────────────────────────────────
   The marketing markup is laid out with desktop inline styles; these media
   queries reshape it for tablet/phone. !important is needed to win over the
   element-level inline styles. */

/* Tablet: features collapse to two columns. */
@media (max-width: 1024px) {
  .landing .lp-features-grid { grid-template-columns: repeat(2, 1fr) !important; }
}

/* Phone: single-column, tighter padding, wrapping button rows, hidden nav links. */
@media (max-width: 640px) {
  .landing .lp-nav { padding: 0 16px !important; }
  .landing .lp-nav-links { display: none !important; }
  .landing .lp-nav-cta { gap: 8px !important; }
  .landing .lp-nav-cta button { padding: 7px 14px !important; font-size: 13px !important; }

  .landing .lp-hero { padding: 92px 20px 56px !important; }
  .landing .lp-sub { font-size: 16px !important; }
  .landing .lp-btn-row {
    width: 100% !important;
    flex-wrap: wrap !important;
    justify-content: center !important;
    gap: 10px !important;
    margin-bottom: 48px !important;
  }
  .landing .lp-btn-row button,
  .landing .lp-btn-row a { flex: 1 1 160px; justify-content: center; }

  .landing .lp-features { padding: 0 20px 64px !important; }
  .landing .lp-features-grid { grid-template-columns: 1fr !important; }

  .landing .lp-steps { padding: 0 20px 64px !important; }
  .landing .lp-steps-row { flex-direction: column !important; align-items: center !important; gap: 36px !important; }
  .landing .lp-steps-line { display: none !important; }
  .landing .lp-step { max-width: 100% !important; }

  .landing .lp-cta { padding: 56px 20px 80px !important; }

  .landing .lp-footer {
    padding: 24px 20px !important;
    justify-content: center !important;
    text-align: center !important;
  }
}
</style>
