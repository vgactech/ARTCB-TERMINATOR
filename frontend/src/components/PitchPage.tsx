/**
 * PitchPage — ARTCB TERMINATOR FORENSIC
 * 
 * Page pitch jury : Pourquoi / Quoi / Pour qui
 * Audience cible : banques, juristes, régulateurs, juges hackathon
 */
import { motion } from 'framer-motion'
import {
  ShieldCheck, AlertTriangle, FileText, Scale,
  Building2, Gavel, TrendingUp, Lock,
  CheckCircle2, ArrowRight, Zap, Globe,
} from 'lucide-react'

type CardProps = {
  icon: React.ReactNode
  title: string
  children: React.ReactNode
  accent?: string
}

function Card({ icon, title, children, accent = 'border-white/8' }: CardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-2xl border ${accent} bg-slate-950/60 p-6`}
    >
      <div className="flex items-start gap-4">
        <div className="shrink-0 mt-0.5">{icon}</div>
        <div>
          <h3 className="font-bold text-white text-base mb-2">{title}</h3>
          <div className="text-sm text-slate-400 leading-relaxed space-y-1">{children}</div>
        </div>
      </div>
    </motion.div>
  )
}

function Stat({ value, label, sub }: { value: string; label: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-white/8 bg-slate-950/50 p-5 text-center">
      <p className="text-3xl font-bold text-emerald-300">{value}</p>
      <p className="text-sm font-semibold text-white mt-1">{label}</p>
      {sub && <p className="text-[11px] text-slate-500 mt-0.5">{sub}</p>}
    </div>
  )
}

function Step({ n, label, detail }: { n: number; label: string; detail: string }) {
  return (
    <div className="flex items-start gap-3">
      <div className="shrink-0 flex size-7 items-center justify-center rounded-full border border-emerald-400/30 bg-emerald-400/10 text-emerald-300 text-xs font-bold">{n}</div>
      <div>
        <p className="text-sm font-semibold text-white">{label}</p>
        <p className="text-xs text-slate-500 mt-0.5">{detail}</p>
      </div>
    </div>
  )
}

export function PitchPage() {
  return (
    <div className="space-y-12 pb-12">

      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <motion.section
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl border border-emerald-400/20 bg-[linear-gradient(135deg,#0a1f17_0%,#0b1b30_60%,#0a1627_100%)] p-8 sm:p-10 relative overflow-hidden"
      >
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_80%_20%,rgba(16,185,129,0.12),transparent_50%)]" />
        <div className="relative">
          <div className="flex items-center gap-2 mb-4">
            <ShieldCheck size={20} className="text-emerald-300" />
            <span className="font-mono text-[11px] font-bold tracking-[0.2em] text-emerald-300">ARTCB TERMINATOR FORENSIC</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-white leading-tight max-w-3xl">
            La première plateforme de{' '}
            <span className="text-emerald-300">sécurité forensique</span>{' '}
            pour agents IA dans les processus bancaires et juridiques
          </h1>
          <p className="mt-4 text-slate-400 text-base max-w-2xl leading-relaxed">
            Chaque décision d'un agent IA est interceptée, tracée cryptographiquement
            et auditée en temps réel — avant toute exécution. Les attaques sont bloquées
            avec preuve. Les rapports sont générés automatiquement.
          </p>
          <div className="mt-6 flex flex-wrap gap-2">
            {['Hackathon ESSEC 2026', 'AWS Bedrock', 'Blockchain ARTCB', 'Guardian Engine R0', 'KYC Forensic'].map(tag => (
              <span key={tag} className="px-3 py-1 rounded-full border border-emerald-400/20 bg-emerald-400/5 text-emerald-300 text-xs font-semibold">{tag}</span>
            ))}
          </div>
        </div>
      </motion.section>

      {/* ── Pourquoi ──────────────────────────────────────────────────────── */}
      <section>
        <div className="flex items-center gap-3 mb-6">
          <AlertTriangle size={18} className="text-amber-300" />
          <h2 className="text-xl font-bold text-white">Pourquoi — Le problème</h2>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <Card
            icon={<AlertTriangle size={22} className="text-amber-300" />}
            title="Les agents IA sont des vecteurs d'attaque invisibles"
            accent="border-amber-400/20"
          >
            <p>Les pipelines d'IA modernes (RAG, agents, orchestrateurs) exécutent des actions à la place de l'humain : signature de transactions, accès aux données clients, envoi de documents.</p>
            <p className="mt-2">Un attaquant peut injecter des instructions malveillantes dans le flux de l'agent — <strong className="text-amber-200">sans que personne ne s'en aperçoive avant que le dommage soit fait.</strong></p>
          </Card>

          <Card
            icon={<Scale size={22} className="text-rose-300" />}
            title="Le vide juridique et réglementaire"
            accent="border-rose-400/20"
          >
            <p>Aucun standard actuel (RGPD, DSP2, DORA, MiFID II) ne couvre la <strong className="text-rose-200">traçabilité forensique des décisions d'agents IA.</strong></p>
            <p className="mt-2">En cas de litige ou d'incident, il est impossible de prouver <em>quel agent a décidé quoi, quand, et pourquoi</em> — sans une piste d'audit cryptographique.</p>
          </Card>

          <Card
            icon={<Building2 size={22} className="text-sky-300" />}
            title="Impact direct pour les banques"
            accent="border-sky-400/20"
          >
            <ul className="space-y-1.5">
              {[
                'KYC automatisé sans garde-fou = risque de blanchiment non détecté',
                'Signature électronique sans contrôle = fraude à grande échelle',
                'Chatbots conseil sans audit = responsabilité bancaire engagée',
                'Coût d\'un incident IA non tracé : 5–50M€ + sanctions BCB/AMF',
              ].map(item => (
                <li key={item} className="flex items-start gap-2">
                  <ArrowRight size={12} className="text-sky-300 shrink-0 mt-0.5" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </Card>

          <Card
            icon={<Gavel size={22} className="text-violet-300" />}
            title="Impact direct pour les juristes"
            accent="border-violet-400/20"
          >
            <ul className="space-y-1.5">
              {[
                'Contrats générés par IA sans traçabilité = inopposables',
                'Diligences raisonnables automatisées non auditées = engagement de responsabilité',
                'Due diligence M&A via IA : qui a accédé à quoi et quand ?',
                'Aucune preuve recevable en justice sans intégrité cryptographique',
              ].map(item => (
                <li key={item} className="flex items-start gap-2">
                  <ArrowRight size={12} className="text-violet-300 shrink-0 mt-0.5" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </section>

      {/* ── Quoi ──────────────────────────────────────────────────────────── */}
      <section>
        <div className="flex items-center gap-3 mb-6">
          <ShieldCheck size={18} className="text-emerald-300" />
          <h2 className="text-xl font-bold text-white">Quoi — La solution</h2>
        </div>

        <div className="rounded-2xl border border-emerald-400/20 bg-slate-950/60 p-6 mb-6">
          <p className="text-base text-slate-300 leading-relaxed max-w-3xl">
            <strong className="text-white">ARTCB TERMINATOR FORENSIC</strong> est un Guardian Engine
            qui s'insère <em>entre</em> l'orchestrateur IA et les outils sensibles.
            Il intercepte chaque appel, applique une politique de sécurité, génère une
            preuve cryptographique immuable, et produit un rapport forensique auditables
            par les autorités de contrôle.
          </p>
        </div>

        {/* Architecture visuelle */}
        <div className="rounded-2xl border border-white/8 bg-slate-950/60 p-6 mb-6">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-5">Architecture — flux de traitement</p>
          <div className="flex flex-wrap items-center gap-2 justify-center">
            {[
              { label: 'Agent LLM', sub: 'Attaquant/Légitime', color: 'border-amber-400/30 text-amber-300 bg-amber-400/5' },
              { label: '→', sub: '', color: 'border-none text-slate-600' },
              { label: 'Orchestrator', sub: 'Session Guardian', color: 'border-cyan-400/30 text-cyan-300 bg-cyan-400/5' },
              { label: '→', sub: '', color: 'border-none text-slate-600' },
              { label: 'Propagator', sub: 'Relais causal', color: 'border-sky-400/30 text-sky-300 bg-sky-400/5' },
              { label: '→', sub: '', color: 'border-none text-slate-600' },
              { label: 'Guardian', sub: 'BLOCK/ALLOW', color: 'border-emerald-400/30 text-emerald-300 bg-emerald-400/5' },
              { label: '→', sub: '', color: 'border-none text-slate-600' },
              { label: 'Preuve R0', sub: 'Hash SHA-256', color: 'border-violet-400/30 text-violet-300 bg-violet-400/5' },
              { label: '→', sub: '', color: 'border-none text-slate-600' },
              { label: 'Rapport PDF', sub: 'Recevable', color: 'border-rose-400/30 text-rose-300 bg-rose-400/5' },
            ].map((node) => (
              node.label === '→' ? (
                <span key={Math.random()} className="text-slate-600 text-lg font-light">{node.label}</span>
              ) : (
                <div key={node.label} className={`rounded-xl border px-4 py-2.5 text-center ${node.color}`}>
                  <p className="text-xs font-bold">{node.label}</p>
                  <p className="text-[10px] opacity-70 mt-0.5">{node.sub}</p>
                </div>
              )
            ))}
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[
            {
              icon: <Lock size={20} className="text-emerald-300" />,
              title: 'Interception en temps réel',
              detail: 'Chaque appel d\'outil sensible (wallet.sign, blockchain.broadcast, memory.write) est intercepté AVANT exécution. L\'IA ne peut pas contourner Guardian.',
            },
            {
              icon: <CheckCircle2 size={20} className="text-violet-300" />,
              title: 'Preuve cryptographique R0',
              detail: 'Chaque événement Guardian est haché (SHA-256), chaîné et archivé. Toute altération est détectée. La chaîne est vérifiable indépendamment.',
            },
            {
              icon: <FileText size={20} className="text-sky-300" />,
              title: 'Rapport PDF forensique',
              detail: 'Généré automatiquement à chaque traitement KYC : identité, score, attaques bloquées, chaîne intègre, timestamp. Téléchargeable, imprimable, recevable en justice.',
            },
            {
              icon: <Zap size={20} className="text-amber-300" />,
              title: 'Détection d\'attaques LLM live',
              detail: 'Un LLM attaquant (Claude Bedrock) génère de vraies attaques adversariales. Guardian les bloque toutes. Le jury voit l\'attaque ET le blocage en direct.',
            },
            {
              icon: <Globe size={20} className="text-cyan-300" />,
              title: 'Intégration blockchain ARTCB',
              detail: '3 nœuds actifs (N2/N3/N4, height=1142). Les preuves Guardian peuvent être ancrées on-chain pour une immutabilité absolue.',
            },
            {
              icon: <TrendingUp size={20} className="text-rose-300" />,
              title: 'Dashboard forensic temps réel',
              detail: 'Timeline SSE live, graphe Guardian HUD animé, taux de blocage, indicateurs par phase. Le jury voit tout le processus se dérouler en direct.',
            },
          ].map(item => (
            <Card key={item.title} icon={item.icon} title={item.title}>
              <p>{item.detail}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* ── Scénario KYC ──────────────────────────────────────────────────── */}
      <section>
        <div className="flex items-center gap-3 mb-6">
          <FileText size={18} className="text-sky-300" />
          <h2 className="text-xl font-bold text-white">Scénario prioritaire — KYC Bancaire</h2>
        </div>

        <div className="rounded-2xl border border-sky-400/20 bg-slate-950/60 p-6 mb-4">
          <p className="text-sm text-slate-300 leading-relaxed mb-4">
            Le KYC (Know Your Customer) est l'obligation réglementaire n°1 des banques :
            vérifier l'identité du client avant toute ouverture de compte, crédit ou transaction.
            Avec les agents IA, ce processus est automatisé — et donc exposé à la fraude à grande échelle.
          </p>
          <div className="grid sm:grid-cols-2 gap-6">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Sans Guardian</p>
              <ul className="space-y-2">
                {[
                  'Agent IA accepte une fausse identité',
                  'Signature frauduleuse exécutée automatiquement',
                  'Aucune trace forensique exploitable',
                  'Responsabilité de la banque engagée',
                  'Sanction BCB/AMF : jusqu\'à 10% du CA',
                ].map(item => (
                  <li key={item} className="flex items-start gap-2 text-xs text-rose-300">
                    <span className="shrink-0 mt-0.5">✗</span> {item}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Avec Guardian</p>
              <ul className="space-y-2">
                {[
                  'Identité vérifiée, attaque fraud détectée',
                  'Guardian BLOCK avant signature — outil jamais exécuté',
                  'Preuve cryptographique R0 archivée',
                  'Rapport PDF généré automatiquement',
                  'Audit régulateur : chaîne complète disponible',
                ].map(item => (
                  <li key={item} className="flex items-start gap-2 text-xs text-emerald-300">
                    <span className="shrink-0 mt-0.5">✓</span> {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-white/8 bg-slate-950/60 p-6">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">Déroulé du scénario KYC — visible par le jury en direct</p>
          <div className="grid sm:grid-cols-2 gap-3">
            {[
              { n: 1, label: 'Soumission identité', detail: 'Prénom, nom, n° document, date de naissance' },
              { n: 2, label: 'Session Guardian ouverte', detail: '4 agents instanciés : Orchestrator / Attacker / Propagator / Defender' },
              { n: 3, label: 'Vérification identité', detail: 'Documents validés, cohérence contrôlée' },
              { n: 4, label: 'Attaque LLM générée', detail: 'wallet.sign(destination=fraud.invalid, amount=99999) — fraude KYC simulée' },
              { n: 5, label: 'Propagation causale', detail: 'Requête relayée avec hash de traçabilité' },
              { n: 6, label: 'Guardian BLOCK', detail: 'Outil jamais exécuté — preuve evidence_id générée' },
              { n: 7, label: 'Chaîne R0 vérifiée', detail: 'N événements hachés, chaîne intacte PASS' },
              { n: 8, label: 'Rapport PDF téléchargeable', detail: 'Score 95%, verdict APPROVED, timestamp, sessions ID' },
            ].map(step => (
              <Step key={step.n} {...step} />
            ))}
          </div>
        </div>
      </section>

      {/* ── Pour qui ──────────────────────────────────────────────────────── */}
      <section>
        <div className="flex items-center gap-3 mb-6">
          <Building2 size={18} className="text-cyan-300" />
          <h2 className="text-xl font-bold text-white">Pour qui — Les utilisateurs cibles</h2>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {[
            {
              icon: <Building2 size={24} className="text-sky-300" />,
              audience: 'Banques & Institutions financières',
              color: 'border-sky-400/20',
              roles: ['DSI / RSSI', 'Conformité & AML', 'Responsables KYC', 'Auditeurs internes'],
              usecases: [
                'KYC automatisé sécurisé et auditable',
                'Protection des signatures électroniques',
                'Rapport de conformité DORA/AMF automatique',
                'Détection fraude temps réel sur agents IA',
              ],
              regulation: 'DORA · AMF · BCB · DSP2 · LCB-FT',
            },
            {
              icon: <Gavel size={24} className="text-violet-300" />,
              audience: 'Cabinets juridiques & Juristes',
              color: 'border-violet-400/20',
              roles: ['Avocats d\'affaires', 'Juristes M&A', 'Notaires', 'Compliance officers'],
              usecases: [
                'Traçabilité des due diligences IA',
                'Preuves recevables en justice',
                'Audit d\'accès aux data rooms',
                'Responsabilité civile des agents IA documentée',
              ],
              regulation: 'RGPD · eIDAS · NIS2 · Code civil Art. 1366',
            },
            {
              icon: <TrendingUp size={24} className="text-emerald-300" />,
              audience: 'Fintechs & Scale-ups',
              color: 'border-emerald-400/20',
              roles: ['CTO / Tech Lead', 'Product managers IA', 'Équipes sécurité', 'Investisseurs DD'],
              usecases: [
                'Guardian en mode API SaaS',
                'Certifier la sécurité IA pour les clients',
                'Différenciation réglementaire',
                'Due diligence investissement : preuves techniques',
              ],
              regulation: 'AI Act (2024) · ISO 27001 · SOC 2',
            },
          ].map(group => (
            <motion.div
              key={group.audience}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              className={`rounded-2xl border ${group.color} bg-slate-950/60 p-6 space-y-4`}
            >
              <div className="flex items-start gap-3">
                {group.icon}
                <div>
                  <h3 className="font-bold text-white text-sm">{group.audience}</h3>
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    {group.roles.map(r => (
                      <span key={r} className="px-2 py-0.5 rounded-full bg-white/5 border border-white/8 text-[10px] text-slate-400">{r}</span>
                    ))}
                  </div>
                </div>
              </div>

              <div>
                <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2">Cas d'usage</p>
                <ul className="space-y-1.5">
                  {group.usecases.map(u => (
                    <li key={u} className="flex items-start gap-2 text-xs text-slate-400">
                      <CheckCircle2 size={11} className="text-emerald-300 shrink-0 mt-0.5" />
                      {u}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="pt-2 border-t border-white/6">
                <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">Réglementations couvertes</p>
                <p className="font-mono text-[10px] text-slate-400">{group.regulation}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Stats ─────────────────────────────────────────────────────────── */}
      <section>
        <div className="flex items-center gap-3 mb-6">
          <TrendingUp size={18} className="text-emerald-300" />
          <h2 className="text-xl font-bold text-white">Métriques techniques — Guardian Engine</h2>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            { value: '169', label: 'Tests Python', sub: '100% PASS' },
            { value: '27',  label: 'Tests Rust',   sub: 'Guardian Core' },
            { value: '8',   label: 'Composants',   sub: 'C-01 → C-08' },
            { value: '4',   label: 'Agents live',  sub: 'Par session' },
            { value: '3',   label: 'Nœuds ARTCB',  sub: 'N2/N3/N4 actifs' },
            { value: '1142',label: 'Block height',  sub: 'PBFT consensus' },
          ].map(s => <Stat key={s.label} {...s} />)}
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────────────────────── */}
      <section className="rounded-2xl border border-emerald-400/20 bg-[linear-gradient(135deg,#0a1f17_0%,#0b1b30_100%)] p-8 text-center">
        <ShieldCheck size={32} className="text-emerald-300 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-white mb-3">Prêt à démontrer en direct</h2>
        <p className="text-slate-400 text-sm max-w-xl mx-auto mb-6">
          Allez dans l'onglet <strong className="text-white">KYC Forensic</strong> et lancez un traitement.
          En moins de 5 secondes, vous verrez une vraie attaque IA générée, bloquée,
          tracée cryptographiquement et documentée en PDF — en temps réel.
        </p>
        <div className="flex flex-wrap justify-center gap-4 text-xs text-slate-500">
          <span>🏦 Banques &amp; Fintech</span>
          <span>⚖️ Juristes &amp; Compliance</span>
          <span>🔐 Sécurité IA</span>
          <span>📋 Audit &amp; Régulation</span>
          <span>⛓️ Blockchain ARTCB</span>
          <span>☁️ AWS Bedrock</span>
        </div>
      </section>

    </div>
  )
}
