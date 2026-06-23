<script setup>
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route  = useRoute()
const auth   = useAuthStore()

defineProps({
  eventName:   { type: String, default: 'Lyftercon 2025' },
  eventStatus: { type: String, default: 'En vivo' },
})

defineEmits(['register', 'login'])

function goRegister() {
  // Only overwrite redirect when on an event-specific preview (worth returning to).
  // On the generic welcome, the router guard already saved the original destination.
  if (route.params.eventId) auth.setRedirect(route.fullPath)
  router.push({ name: 'register' })
}
function goLogin() {
  if (route.params.eventId) auth.setRedirect(route.fullPath)
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="page">

    <!-- animated background -->
    <div aria-hidden="true" class="preview-bg">
      <div class="bg-grid"></div>
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
      <span class="glyph glyph-1">{ }</span>
      <span class="glyph glyph-2">&lt;/&gt;</span>
      <span class="star star-1"></span>
      <span class="star star-2"></span>
    </div>

    <!-- scrollable content -->
    <div class="content screen-in">

      <!-- ── Hero ── -->
      <section class="hero-section">
        <span class="hero-deco-1" aria-hidden="true">{ }</span>
        <span class="hero-deco-2" aria-hidden="true">&lt;/&gt;</span>

        <div class="logo-row">
          <div class="logo-mark">
            <span class="logo-brace">{</span>
            <div class="logo-bars">
              <span class="logo-bar bar-1"></span>
              <span class="logo-bar bar-2"></span>
              <span class="logo-bar bar-3"></span>
            </div>
            <span class="logo-brace">}</span>
          </div>
          <span class="logo-name">BadgeApp</span>
          <div class="live-pill">
            <span class="live-dot"></span>
            <span class="live-label">{{ eventStatus }}</span>
          </div>
        </div>

        <h1 class="hero-title">Cada sesión<br>es un badge.<br>Cada badge,<br>un paso al premio.</h1>
        <p class="hero-sub">Llegás a una sesión, escaneás el QR de la sala y el badge aparece en tu perfil al instante. Sin apps extra, sin fricción.</p>

        <button type="button" class="cta-btn" @click="goRegister">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
            <line x1="19" y1="8" x2="19" y2="14"/><line x1="22" y1="11" x2="16" y2="11"/>
          </svg>
          Crear cuenta gratis
        </button>
        <p class="hero-signin">
          ¿Ya tenés cuenta?
          <button type="button" class="hero-signin-link" @click="goLogin">Iniciar sesión</button>
        </p>
      </section>

      <!-- ── Badges de ejemplo ── -->
      <section class="info-section">
        <span class="section-title">Así se ven los badges</span>
        <p class="section-body">Cada evento tiene sus propios badges. Este es un ejemplo de cómo lucen los desbloqueados — los demás se revelan cuando escaneás.</p>

        <div class="badge-row">
          <div class="badge-sample" style="animation:rise .4s both .04s">
            <div class="badge-circle" style="border-color:#71ceff;background:rgba(113,206,255,.11);box-shadow:0 0 16px -5px #71ceff">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#71ceff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            </div>
            <span class="badge-label">Apertura</span>
          </div>
          <div class="badge-sample" style="animation:rise .4s both .09s">
            <div class="badge-circle" style="border-color:#add195;background:rgba(173,209,149,.11);box-shadow:0 0 16px -5px #add195">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#add195" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
            </div>
            <span class="badge-label">Dev Talk</span>
          </div>
          <div class="badge-sample" style="animation:rise .4s both .14s">
            <div class="badge-circle" style="border-color:#d798e7;background:rgba(215,152,231,.11);box-shadow:0 0 16px -5px #d798e7">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#d798e7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
            </div>
            <span class="badge-label">Destacado</span>
          </div>
          <div class="badge-sample badge-sample--locked">
            <div class="badge-circle badge-circle--locked">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            </div>
            <span class="badge-label">+más</span>
          </div>
        </div>
      </section>

      <!-- ── Premio ── -->
      <section class="prize-section">
        <div class="prize-row">
          <div class="prize-icon-wrap">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ffcc8b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M20 12V22H4V12"/><path d="M22 7H2v5h20V7z"/><path d="M12 22V7"/>
              <path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"/><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"/>
            </svg>
          </div>
          <div>
            <span class="prize-title">Hay un premio esperándote</span>
            <p class="prize-desc">El organizador preparó una recompensa para quienes completen todos los badges. Se revela automáticamente al obtener el último.</p>
          </div>
        </div>
      </section>

      <!-- ── FAQ ── -->
      <section class="faq-section">
        <span class="section-title">Preguntas frecuentes</span>
        <div class="faq-list">
          <div class="faq-item" style="animation:rise .4s both .04s">
            <p class="faq-q">¿Necesito descargar una app?</p>
            <p class="faq-a">No. Corre en el navegador de tu celular. Solo escaneás, te registrás y empezás.</p>
          </div>
          <div class="faq-item" style="animation:rise .4s both .09s">
            <p class="faq-q">¿Puedo canjear un badge más de una vez?</p>
            <p class="faq-a">No. Cada QR es de un solo uso por cuenta. Si ya escaneaste esa sesión, el sistema te avisa.</p>
          </div>
          <div class="faq-item" style="animation:rise .4s both .14s">
            <p class="faq-q">¿Los badges quedan guardados?</p>
            <p class="faq-a">Sí. Tu colección queda en tu cuenta y podés verla después del evento, organizada por evento.</p>
          </div>
        </div>
      </section>

      <!-- ── Footer CTA ── -->
      <section class="footer-cta">
        <p class="footer-text">El registro es gratuito<br>y tarda menos de un minuto.</p>
        <button type="button" class="cta-btn" style="margin-bottom:0" @click="goRegister">
          Empezar a coleccionar
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
          </svg>
        </button>
        <p class="footer-note">Sin descarga · Solo tu celular</p>
      </section>

    </div>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Montserrat:wght@300;400;500;600&display=swap');
</style>

<style scoped>
@keyframes screenIn   { from{opacity:0;transform:translateY(14px) scale(.985)} to{opacity:1;transform:none} }
@keyframes rise       { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:none} }
@keyframes float1     { 0%,100%{transform:translateY(0) rotate(-8deg)} 50%{transform:translateY(-11px) rotate(-8deg)} }
@keyframes float2     { 0%,100%{transform:translateY(0) rotate(10deg)} 50%{transform:translateY(9px) rotate(10deg)} }
@keyframes orbDrift1  { 0%,100%{transform:translate(0,0) scale(1)} 33%{transform:translate(40px,-30px) scale(1.1)} 66%{transform:translate(-20px,20px) scale(.94)} }
@keyframes orbDrift2  { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-50px,40px) scale(1.15)} }
@keyframes orbDrift3  { 0%,100%{transform:translate(0,0)} 40%{transform:translate(30px,40px) scale(1.08)} 75%{transform:translate(-30px,-20px) scale(.96)} }
@keyframes gridPan    { from{background-position:0 0} to{background-position:56px 56px} }
@keyframes glyphFall  { 0%{transform:translateY(-40px);opacity:0} 12%{opacity:.4} 88%{opacity:.4} 100%{transform:translateY(200vh);opacity:0} }
@keyframes twinkle    { 0%,100%{opacity:.1} 50%{opacity:.6} }
@keyframes auroraHue  { 0%,100%{filter:hue-rotate(0deg)} 50%{filter:hue-rotate(28deg)} }
@keyframes codebar    { 0%,100%{transform:scaleX(.45);opacity:.55} 50%{transform:scaleX(1);opacity:1} }
@keyframes pulse      { 0%,100%{opacity:.4} 50%{opacity:1} }

/* ── Page ── */
.page {
  position: relative;
  min-height: 100dvh;
  background: radial-gradient(130% 120% at 50% -10%, #14161f 0%, #0a0b10 58%, #06070a 100%);
  overflow-x: hidden;
}

/* ── Background ── */
.preview-bg { position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden; }
.bg-grid {
  position:absolute;inset:-40px;
  background-image:linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px);
  background-size:56px 56px;
  mask-image:radial-gradient(120% 90% at 50% 30%,#000 0%,transparent 75%);
  -webkit-mask-image:radial-gradient(120% 90% at 50% 30%,#000 0%,transparent 75%);
  animation:gridPan 7s linear infinite;
}
.orb { position:absolute;border-radius:50%; }
.orb-1 { top:-100px;left:-60px;width:360px;height:360px;background:radial-gradient(circle at 30% 30%,#71ceff,transparent 68%);filter:blur(70px);opacity:.45;animation:orbDrift1 18s ease-in-out infinite,auroraHue 14s ease-in-out infinite; }
.orb-2 { bottom:-100px;right:-60px;width:380px;height:380px;background:radial-gradient(circle at 60% 40%,#d798e7,transparent 68%);filter:blur(80px);opacity:.38;animation:orbDrift2 22s ease-in-out infinite; }
.orb-3 { top:40%;right:4%;width:260px;height:260px;background:radial-gradient(circle at 50% 50%,#ffcc8b,transparent 70%);filter:blur(75px);opacity:.25;animation:orbDrift3 26s ease-in-out infinite; }
.glyph { position:absolute;top:0;font-family:'Space Grotesk',sans-serif;font-weight:700; }
.glyph-1 { left:9%;font-size:18px;color:rgba(113,206,255,.4);animation:glyphFall 13s linear infinite; }
.glyph-2 { left:68%;font-size:15px;color:rgba(215,152,231,.35);animation:glyphFall 17s linear infinite 5s; }
.star { position:absolute;border-radius:50%;background:#fff; }
.star-1 { left:16%;top:22%;width:3px;height:3px;animation:twinkle 4s ease-in-out infinite; }
.star-2 { left:82%;top:18%;width:2px;height:2px;animation:twinkle 5s ease-in-out infinite 1s; }

/* ── Content ── */
.content { position:relative;z-index:1;max-width:480px;margin:0 auto; }
.screen-in { animation:screenIn .5s cubic-bezier(.2,.7,.2,1) both; }

/* ── Hero ── */
.hero-section {
  position:relative;padding:32px 22px 32px;
  background:radial-gradient(120% 70% at 0% 0%,rgba(113,206,255,.16),transparent 52%),
             radial-gradient(120% 80% at 100% 100%,rgba(215,152,231,.16),transparent 55%),
             #0c0e14;
  overflow:hidden;
}
.hero-deco-1 { position:absolute;top:28px;right:8px;font-family:'Space Grotesk',sans-serif;font-size:46px;font-weight:700;color:rgba(113,206,255,.06);animation:float1 7s ease-in-out infinite; }
.hero-deco-2 { position:absolute;bottom:36px;left:4px;font-family:'Space Grotesk',sans-serif;font-size:28px;font-weight:700;color:rgba(215,152,231,.06);animation:float2 8s ease-in-out infinite; }

.logo-row  { display:flex;align-items:center;gap:8px;margin-bottom:22px; }
.logo-mark { width:32px;height:32px;border-radius:9px;background:linear-gradient(135deg,#71ceff,#d798e7 52%,#ffcc8b);display:flex;align-items:center;justify-content:center;box-shadow:0 6px 18px rgba(113,206,255,.32);flex-shrink:0; }
.logo-brace{ font-family:'Space Grotesk',sans-serif;font-weight:700;color:#10131a;font-size:10px; }
.logo-bars { display:flex;flex-direction:column;gap:1.5px;margin:0 1px; }
.logo-bar  { height:1.5px;border-radius:2px;background:#10131a;transform-origin:left; }
.bar-1 { width:7px;animation:codebar 2.4s ease-in-out infinite; }
.bar-2 { width:5px;animation:codebar 2.4s ease-in-out infinite .3s; }
.bar-3 { width:6px;animation:codebar 2.4s ease-in-out infinite .6s; }
.logo-name { font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:14px;color:#fff; }

.live-pill { margin-left:auto;display:inline-flex;align-items:center;gap:4px;background:rgba(113,206,255,.1);border:1px solid rgba(113,206,255,.22);border-radius:20px;padding:3px 9px; }
.live-dot  { width:5px;height:5px;border-radius:50%;background:#71ceff;animation:pulse 2s ease-in-out infinite; }
.live-label{ font-family:'Montserrat',sans-serif;font-size:9.5px;font-weight:500;color:#71ceff; }

.hero-title { font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:23px;line-height:1.12;color:#fff;margin-bottom:10px;letter-spacing:-.02em; }
.hero-sub   { font-family:'Montserrat',sans-serif;font-size:12px;color:rgba(255,255,255,.52);line-height:1.7;margin-bottom:22px; }

.cta-btn {
  display:flex;align-items:center;justify-content:center;gap:6px;width:100%;
  background:linear-gradient(135deg,#5b8def,#71ceff);color:#fff;border:none;
  border-radius:13px;padding:13px;font-family:'Space Grotesk',sans-serif;
  font-weight:600;font-size:13px;cursor:pointer;
  box-shadow:0 10px 26px -8px #71ceff;margin-bottom:10px;
}
.hero-signin { text-align:center;font-family:'Montserrat',sans-serif;font-size:10.5px;color:rgba(255,255,255,.3); }
.hero-signin-link { color:#71ceff;font-weight:600;background:none;border:none;cursor:pointer;padding:0;font-family:inherit;font-size:inherit; }

/* ── Shared section base ── */
.info-section,
.faq-section { padding:32px 22px 28px;background:#0b0d13;border-top:2px solid rgba(255,255,255,.05); }
.prize-section { padding:28px 22px;background:radial-gradient(120% 70% at 100% 0%,rgba(215,152,231,.1),transparent 54%),#0c0b13;border-top:2px solid rgba(255,255,255,.05); }
.footer-cta { padding:32px 22px 36px;background:#0c0e14;border-top:2px solid rgba(255,255,255,.05);text-align:center; }

.section-title { font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:14px;color:#fff;display:block;margin-bottom:8px; }
.section-body  { font-family:'Montserrat',sans-serif;font-size:12px;color:rgba(255,255,255,.45);line-height:1.7;margin-bottom:22px; }

/* ── Badge row ── */
.badge-row { display:flex;gap:14px;align-items:flex-start; }
.badge-sample { display:flex;flex-direction:column;align-items:center;gap:6px; }
.badge-sample--locked { opacity:.3; }
.badge-circle {
  width:52px;height:52px;border-radius:50%;border:2px solid transparent;
  display:flex;align-items:center;justify-content:center;
}
.badge-circle--locked {
  border:2px dashed rgba(255,255,255,.2);background:transparent;box-shadow:none;
}
.badge-label { font-family:'Montserrat',sans-serif;font-size:9.5px;color:rgba(255,255,255,.5);text-align:center; }

/* ── Prize ── */
.prize-row { display:flex;align-items:flex-start;gap:12px; }
.prize-icon-wrap {
  width:40px;height:40px;flex-shrink:0;margin-top:2px;
  background:rgba(255,204,139,.1);border:1px solid rgba(255,204,139,.22);
  border-radius:11px;display:flex;align-items:center;justify-content:center;
}
.prize-title { font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:13.5px;color:#fff;display:block;margin-bottom:5px; }
.prize-desc  { font-family:'Montserrat',sans-serif;font-size:12px;color:rgba(255,255,255,.48);line-height:1.7; }

/* ── FAQ ── */
.faq-list { display:flex;flex-direction:column;gap:14px;margin-top:18px; }
.faq-item { padding:14px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:12px; }
.faq-q { font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:12.5px;color:#fff;margin-bottom:4px; }
.faq-a { font-family:'Montserrat',sans-serif;font-size:11.5px;color:rgba(255,255,255,.48);line-height:1.65; }

/* ── Footer ── */
.footer-text { font-family:'Montserrat',sans-serif;font-size:11.5px;color:rgba(255,255,255,.38);line-height:1.7;margin-bottom:16px; }
.footer-note { font-family:'Montserrat',sans-serif;font-size:10px;color:rgba(255,255,255,.2);margin-top:10px; }
</style>
