import React, { useState, useEffect } from "react";
import {
  FileSignature,
  Plus,
  FileText,
  FolderOpen,
  Download,
  Trash2,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  Copy,
  Check,
  Calendar,
  Users,
  Scale,
  ShieldAlert,
  RefreshCw,
  BookOpen,
  Info,
  ExternalLink,
} from "lucide-react";
import { api } from "../api/client";
import { SupremeCourt3DCanvas } from "../components/SupremeCourt3DCanvas";
import {
  PetitionDraftListItem,
  PetitionFormData,
  PetitionResponse,
  PetitionType,
} from "../types";

interface Props {
  onNavigateToCase?: (documentId: number, paraNo?: number | null) => void;
}

const PETITION_TYPES: Array<{
  id: PetitionType;
  title: string;
  code: string;
  court: string;
  desc: string;
  badge: string;
}> = [
  {
    id: "writ_petition",
    title: "Writ Petition",
    code: "Art. 32 / 226",
    court: "Supreme Court / High Court",
    desc: "Enforcement of Fundamental Rights (Articles 14, 19, 21) or judicial review of arbitrary administrative action.",
    badge: "Constitutional",
  },
  {
    id: "bail_application",
    title: "Bail Application",
    code: "CrPC 437/438/439 • BNSS 480/482/483",
    court: "High Court / Sessions Court",
    desc: "Regular, interim, or anticipatory bail petition grounded in the triple test and liberty jurisprudence.",
    badge: "Criminal Liberty",
  },
  {
    id: "pil",
    title: "Public Interest Litigation (PIL)",
    code: "Pro Bono Publico",
    court: "Supreme Court / High Court",
    desc: "Redressal of public injury, enforcement of public duty, or protection of marginalized constitutional rights.",
    badge: "Public Law",
  },
  {
    id: "civil_petition",
    title: "Civil Petition / Application",
    code: "CPC S. 115 / O. 39",
    court: "High Court / District Court",
    desc: "Civil revision, review, or miscellaneous application for temporary injunction and balance of convenience.",
    badge: "Civil Jurisdiction",
  },
  {
    id: "criminal_revision",
    title: "Criminal Revision Petition",
    code: "CrPC 397/401 • BNSS 438/442",
    court: "High Court / Sessions Court",
    desc: "Challenging patent illegality, perversity of findings, or procedural irregularity in lower court criminal orders.",
    badge: "Criminal Review",
  },
  {
    id: "custom_petition",
    title: "Custom Legal Petition",
    code: "Statutory / Representation",
    court: "Any Competent Court / Tribunal",
    desc: "Tailored legal pleading with structured cause title, statement of facts, legal grounds, prayers, and affidavit.",
    badge: "Specialized Pleading",
  },
];

const INITIAL_FORM_DATA: PetitionFormData = {
  petition_type: "writ_petition",
  court_level: "supreme_court",
  court_name: "Supreme Court of India",
  state_ut: "Delhi",
  category: "constitutional",
  case_number: "",
  statutory_provisions: "Article 32 of the Constitution of India",
  petitioners: [
    {
      name: "Mohan Lal",
      age: "48",
      relation: "S/o Late Shri Ram Lal",
      address: "House No. 42, Civil Lines, New Delhi 110054",
      role: "Petitioner No. 1",
      advocate_name: "Adv. Rajesh Sharma",
      advocate_bar_id: "D/1234/2010",
    },
  ],
  respondents: [
    {
      name: "Municipal Corporation of Delhi & Anr.",
      address: "Through Commissioner, Civic Centre, Minto Road, New Delhi 110002",
      role: "Respondent No. 1",
    },
  ],
  dispute_background:
    "Arbitrary demolition notice issued without prior show-cause notice or affording a reasonable opportunity of hearing, directly infringing Articles 14, 19(1)(e), and 21 of the Constitution of India.",
  events: [
    {
      date: "10.10.2026",
      description: "Demolition notice pasted on subject premises without prior show cause notice or hearing.",
    },
    {
      date: "14.10.2026",
      description: "Petitioner submitted detailed representation with registered title deeds; no hearing afforded.",
    },
  ],
  previous_orders: [],
  annexures: [
    {
      mark: "P-1",
      title: "True copy of Impugned Demolition Notice dated 10.10.2026",
      description: "Arbitrary notice without statutory reasons",
    },
    {
      mark: "P-2",
      title: "Registered Sale Deed of subject residential property",
      description: "Proof of lawful ownership and uninterrupted possession since 1998",
    },
  ],
  grounds: [
    "That the impugned action/notice is completely arbitrary and violates the cardinal principle of audi alteram partem.",
    "That the Petitioner has clean title and lawful possession; demolition without due process causes irreparable constitutional injury.",
    "That no efficacious alternative legal remedy exists to avert the imminent threat of dispossession.",
  ],
  rights_infringed: ["Article 14", "Article 19(1)(e)", "Article 21"],
  statutes_applied: ["Constitution of India, 1950", "Delhi Municipal Corporation Act, 1957"],
  urgency_reason: "Demolition threatened within 48 hours; immediate interim protection is imperative to prevent dispossession.",
  limitation_explanation: "Petition filed promptly within 14 days of receipt of impugned notice; no delay.",
  main_prayers: [
    "Issue a Writ of Certiorari or any other appropriate writ quashing the impugned demolition notice dated 10.10.2026;",
    "Direct the Respondent authorities not to disturb the peaceful possession and enjoyment of the subject property.",
  ],
  interim_prayers: [
    "Pass an ex-parte ad-interim stay of the operation of the impugned notice dated 10.10.2026 during the pendency of this petition.",
  ],
};

export const PetitionGeneratorPage: React.FC<Props> = ({ onNavigateToCase }) => {
  // Navigation / View State: 'landing' | 'wizard' | 'editor'
  const [view, setView] = useState<"landing" | "wizard" | "editor">("landing");
  const [wizardStep, setWizardStep] = useState<number>(1);

  // Form & Document State
  const [formData, setFormData] = useState<PetitionFormData>(INITIAL_FORM_DATA);
  const [generatedDoc, setGeneratedDoc] = useState<PetitionResponse | null>(null);
  const [activeSectionKey, setActiveSectionKey] = useState<string>("synopsis");
  const [editedSections, setEditedSections] = useState<Record<string, string>>({});

  // Drafts & Management
  const [savedDrafts, setSavedDrafts] = useState<PetitionDraftListItem[]>([]);
  const [loadingDrafts, setLoadingDrafts] = useState<boolean>(false);
  const [generating, setGenerating] = useState<boolean>(false);
  const [regenerating, setRegenerating] = useState<boolean>(false);
  const [regenInstruction, setRegenInstruction] = useState<string>("");
  const [showRegenModal, setShowRegenModal] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [copiedDoc, setCopiedDoc] = useState<boolean>(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  // Load Saved Drafts on Mount
  useEffect(() => {
    loadDrafts();
  }, []);

  const loadDrafts = async () => {
    setLoadingDrafts(true);
    try {
      const list = await api.listPetitions();
      setSavedDrafts(list);
    } catch {
      // Local fallback
    } finally {
      setLoadingDrafts(false);
    }
  };

  const handleStartNew = () => {
    setFormData(INITIAL_FORM_DATA);
    setWizardStep(1);
    setView("wizard");
    setErrorMessage(null);
  };

  const handleOpenDraft = async (id: number) => {
    try {
      const draft = await api.getPetition(id);
      setGeneratedDoc(draft);
      setEditedSections(draft.sections || {});
      setActiveSectionKey(Object.keys(draft.sections || {})[0] || "synopsis");
      setView("editor");
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to load saved draft");
    }
  };

  const handleDeleteDraft = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this petition draft?")) return;
    try {
      await api.deletePetition(id);
      setSavedDrafts((prev) => prev.filter((d) => d.id !== id));
      if (generatedDoc?.id === id) {
        setView("landing");
        setGeneratedDoc(null);
      }
    } catch (err: any) {
      alert("Failed to delete draft: " + err.message);
    }
  };

  // Generate Draft Action
  const handleGenerate = async () => {
    setGenerating(true);
    setErrorMessage(null);
    try {
      const response = await api.generatePetition(formData);
      setGeneratedDoc(response);
      setEditedSections(response.sections);
      setActiveSectionKey("synopsis");
      setView("editor");
      loadDrafts(); // refresh drafts list in background
    } catch (err: any) {
      setErrorMessage(err.message || "Drafting engine encountered an error. Please verify input fields.");
    } finally {
      setGenerating(false);
    }
  };

  // Section Regeneration Action
  const handleRegenerateCurrentSection = async () => {
    if (!generatedDoc) return;
    setRegenerating(true);
    try {
      const res = await api.regenerateSection({
        petition_id: generatedDoc.id || undefined,
        petition_type: generatedDoc.petition_type,
        section_key: activeSectionKey,
        custom_instruction: regenInstruction.trim() || undefined,
        current_sections: editedSections,
        draft_metadata: {},
      });
      setEditedSections((prev) => ({ ...prev, [activeSectionKey]: res.content }));
      setShowRegenModal(false);
      setRegenInstruction("");
      setSaveSuccessMsg(`Section '${activeSectionKey}' updated with verified precedents!`);
      setTimeout(() => setSaveSuccessMsg(null), 3500);
    } catch (err: any) {
      alert("Failed to regenerate section: " + err.message);
    } finally {
      setRegenerating(false);
    }
  };

  // Save Edits to Backend
  const handleSaveDraft = async () => {
    if (!generatedDoc?.id) return;
    try {
      await api.updatePetition(generatedDoc.id, {
        sections: editedSections,
        status: "reviewed",
      });
      setSaveSuccessMsg("All document revisions saved successfully!");
      setTimeout(() => setSaveSuccessMsg(null), 3000);
      loadDrafts();
    } catch (err: any) {
      alert("Save failed: " + err.message);
    }
  };

  // Copy Full Document
  const handleCopyFull = () => {
    const full = Object.values(editedSections).join("\n\n" + "=".repeat(60) + "\n\n");
    navigator.clipboard.writeText(full);
    setCopiedDoc(true);
    setTimeout(() => setCopiedDoc(false), 2500);
  };

  // Download DOCX
  const handleDownloadDocx = async () => {
    if (generatedDoc?.id) {
      window.open(api.getDocxExportUrl(generatedDoc.id), "_blank");
    } else {
      const blob = await api.exportDirectDocx({
        sections: editedSections,
        title: generatedDoc?.title || "Petition_Draft",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${generatedDoc?.petition_type || "petition"}_draft.docx`;
      a.click();
    }
  };

  // Download PDF
  const handleDownloadPdf = async () => {
    if (generatedDoc?.id) {
      window.open(api.getPdfExportUrl(generatedDoc.id), "_blank");
    } else {
      const blob = await api.exportDirectPdf({
        sections: editedSections,
        title: generatedDoc?.title || "Petition_Draft",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${generatedDoc?.petition_type || "petition"}_draft.pdf`;
      a.click();
    }
  };

  return (
    <div className="max-w-[1440px] mx-auto px-4 sm:px-6 py-6 font-sans">
      {/* ========================================================
          VIEW 1: LANDING & DASHBOARD
          ======================================================== */}
      {view === "landing" && (
        <div className="space-y-8">
          {/* Hero Banner with 3D Supreme Court Canvas */}
          <div className="bg-[#edf2ec] border-2 border-[#c2d4c0] rounded-2xl p-6 sm:p-8 shadow-xs flex flex-col md:flex-row items-center justify-between gap-6 relative overflow-hidden">
            <div className="flex-1 max-w-2xl z-10 space-y-3">
              <div className="inline-flex items-center space-x-2 bg-[#dcfce7] text-[#14532d] border border-[#86efac] px-3.5 py-1 rounded-full text-xs font-bold shadow-3xs">
                <Sparkles className="h-3.5 w-3.5 text-[#15803d]" />
                <span>Citation-Grounded Indian Legal Drafting</span>
              </div>

              <h2 className="text-3xl sm:text-4xl font-serif font-bold text-[#071e17] tracking-tight leading-tight">
                Petition &amp; Pleading Generator
              </h2>

              <p className="text-sm sm:text-base text-slate-800 font-medium leading-relaxed">
                Draft court-compliant Writ Petitions, Bail Applications, PILs, and Revisions formatted
                under Supreme Court and High Court rules, grounded in verified precedent citations.
              </p>

              <div className="flex flex-wrap items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={handleStartNew}
                  className="flex items-center space-x-2 px-6 py-3 rounded-xl bg-[#071e17] hover:bg-[#0f2c24] text-white font-bold text-sm shadow-md transition-all hover:shadow-lg cursor-pointer"
                >
                  <Plus className="h-4 w-4 stroke-[2.5]" />
                  <span>Create New Petition</span>
                </button>

                <div className="text-xs font-semibold text-slate-700 flex items-center space-x-1.5 pl-2">
                  <ShieldAlert className="h-4 w-4 text-[#b45309]" />
                  <span>Requires independent advocate review before filing</span>
                </div>
              </div>
            </div>

            <div className="shrink-0 flex items-center justify-center z-10">
              <SupremeCourt3DCanvas className="w-64 h-44" />
            </div>
          </div>

          {/* 6 Supported Document Types Overview Grid */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-950 flex items-center space-x-2">
                <Scale className="h-5 w-5 text-[#071e17]" />
                <span>Supported Petition Frameworks</span>
              </h3>
              <span className="text-xs font-bold text-slate-600">
                Indian Court Rules &bull; CPC &bull; CrPC &bull; BNSS
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {PETITION_TYPES.map((pt) => (
                <div
                  key={pt.id}
                  onClick={() => {
                    setFormData({ ...formData, petition_type: pt.id });
                    setView("wizard");
                    setWizardStep(1);
                  }}
                  className="bg-white border-2 border-slate-200 hover:border-[#071e17] rounded-xl p-5 shadow-xs transition-all hover:shadow-md cursor-pointer space-y-2.5 group"
                >
                  <div className="flex items-start justify-between">
                    <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-[#f8fafc] text-slate-800 border border-slate-300">
                      {pt.badge}
                    </span>
                    <span className="text-xs font-mono font-bold text-[#78350f] bg-[#faeae1] border border-[#f3d3be] px-2 py-0.5 rounded">
                      {pt.code}
                    </span>
                  </div>

                  <h4 className="font-bold text-base text-slate-950 group-hover:text-[#0f2c24] transition-colors">
                    {pt.title}
                  </h4>

                  <p className="text-xs text-slate-700 font-medium leading-relaxed">
                    {pt.desc}
                  </p>

                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-[#071e17]">
                    <span>{pt.court}</span>
                    <span className="flex items-center space-x-1 group-hover:translate-x-1 transition-transform">
                      <span>Draft Now</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Saved Drafts Section */}
          <div className="bg-white border-2 border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div className="flex items-center space-x-2">
                <FolderOpen className="h-5 w-5 text-[#071e17]" />
                <h3 className="font-bold text-lg text-slate-950">
                  Recent Saved Drafts ({savedDrafts.length})
                </h3>
              </div>
              <button
                type="button"
                onClick={loadDrafts}
                className="text-xs font-bold text-slate-600 hover:text-slate-950 flex items-center space-x-1"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${loadingDrafts ? "animate-spin" : ""}`} />
                <span>Refresh</span>
              </button>
            </div>

            {savedDrafts.length === 0 ? (
              <div className="text-center py-12 space-y-3 text-slate-600">
                <FileSignature className="h-10 w-10 mx-auto text-slate-400 stroke-[1.5]" />
                <p className="text-sm font-semibold text-slate-800">
                  No saved drafts yet. Click &quot;Create New Petition&quot; above to draft your first pleading.
                </p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {savedDrafts.map((d) => (
                  <div
                    key={d.id}
                    onClick={() => handleOpenDraft(d.id)}
                    className="py-3.5 px-3 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 hover:bg-slate-50 rounded-xl transition-colors cursor-pointer"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-xs font-bold text-amber-950 bg-[#faeae1] border border-[#f3d3be] px-2 py-0.5 rounded">
                          #{d.id}
                        </span>
                        <h4 className="font-bold text-sm text-slate-950 hover:underline">
                          {d.title}
                        </h4>
                        <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-300 capitalize">
                          {d.status}
                        </span>
                      </div>
                      <p className="text-xs font-medium text-slate-600">
                        {d.court_name} &bull; {d.petitioner_name} v. {d.respondent_name} &bull; Updated: {d.updated_at ? new Date(d.updated_at).toLocaleDateString() : "Recent"}
                      </p>
                    </div>

                    <div className="flex items-center space-x-2 shrink-0">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          window.open(api.getDocxExportUrl(d.id), "_blank");
                        }}
                        className="px-2.5 py-1 text-xs font-bold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-100 flex items-center space-x-1"
                        title="Download DOCX"
                      >
                        <Download className="h-3.5 w-3.5" />
                        <span>DOCX</span>
                      </button>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          window.open(api.getPdfExportUrl(d.id), "_blank");
                        }}
                        className="px-2.5 py-1 text-xs font-bold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-100 flex items-center space-x-1"
                        title="Download PDF"
                      >
                        <Download className="h-3.5 w-3.5" />
                        <span>PDF</span>
                      </button>
                      <button
                        type="button"
                        onClick={(e) => handleDeleteDraft(e, d.id)}
                        className="p-1.5 text-rose-600 hover:text-rose-800 rounded-lg hover:bg-rose-50"
                        title="Delete Draft"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================
          VIEW 2: MULTI-STEP CREATION WIZARD
          ======================================================== */}
      {view === "wizard" && (
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Wizard Header & Progress Bar */}
          <div className="bg-white border-2 border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-[#78350f] uppercase tracking-wider">
                  Step {wizardStep} of 5
                </span>
                <h3 className="text-xl sm:text-2xl font-bold text-slate-950">
                  {wizardStep === 1 && "Document Framework & Jurisdiction"}
                  {wizardStep === 2 && "Parties & Advocates"}
                  {wizardStep === 3 && "Facts & Chronology (List of Dates)"}
                  {wizardStep === 4 && "Legal Grounds, Rights & Relief"}
                  {wizardStep === 5 && "Review & Generate Court Draft"}
                </h3>
              </div>

              <button
                type="button"
                onClick={() => setView("landing")}
                className="text-xs font-bold text-slate-600 hover:text-slate-950 border border-slate-300 px-3 py-1.5 rounded-xl hover:bg-slate-50"
              >
                &larr; Back to Dashboard
              </button>
            </div>

            {/* Stepper Dots */}
            <div className="grid grid-cols-5 gap-2 pt-1">
              {[
                "1. Document",
                "2. Parties",
                "3. Facts",
                "4. Grounds",
                "5. Review",
              ].map((stepLabel, idx) => {
                const sNum = idx + 1;
                const isComplete = wizardStep > sNum;
                const isCurrent = wizardStep === sNum;
                return (
                  <div
                    key={sNum}
                    onClick={() => setWizardStep(sNum)}
                    className={`cursor-pointer border-t-4 pt-2 text-xs font-bold transition-all ${
                      isComplete
                        ? "border-[#15803d] text-[#15803d]"
                        : isCurrent
                        ? "border-[#071e17] text-[#071e17]"
                        : "border-slate-200 text-slate-400"
                    }`}
                  >
                    <span>{stepLabel}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div className="bg-rose-50 border-2 border-rose-300 text-rose-950 p-4 rounded-xl text-sm font-bold flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-rose-600 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* STEP 1: Document Details */}
          {wizardStep === 1 && (
            <div className="bg-white border-2 border-slate-200 rounded-2xl p-6 shadow-xs space-y-5">
              <div className="space-y-2">
                <label className="block text-xs font-extrabold text-slate-900 uppercase tracking-wider">
                  Select Petition Type
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {PETITION_TYPES.map((pt) => (
                    <label
                      key={pt.id}
                      className={`flex items-start space-x-3 p-3.5 rounded-xl border-2 cursor-pointer transition-all ${
                        formData.petition_type === pt.id
                          ? "border-[#071e17] bg-[#edf2ec] text-[#071e17] font-bold"
                          : "border-slate-200 hover:border-slate-400 text-slate-800"
                      }`}
                    >
                      <input
                        type="radio"
                        name="petition_type"
                        value={pt.id}
                        checked={formData.petition_type === pt.id}
                        onChange={() => setFormData({ ...formData, petition_type: pt.id })}
                        className="mt-1 accent-[#071e17]"
                      />
                      <div>
                        <div className="font-bold text-sm">{pt.title}</div>
                        <div className="text-xs text-slate-600 font-normal">{pt.desc}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider mb-1">
                    Court Level
                  </label>
                  <select
                    value={formData.court_level}
                    onChange={(e) => {
                      const cLev = e.target.value as any;
                      setFormData({
                        ...formData,
                        court_level: cLev,
                        court_name:
                          cLev === "supreme_court"
                            ? "Supreme Court of India"
                            : cLev === "high_court"
                            ? "High Court of Delhi at New Delhi"
                            : "Court of Principal District & Sessions Judge",
                      });
                    }}
                    className="w-full bg-white border-2 border-slate-300 rounded-xl px-3.5 py-2 text-sm font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#071e17]"
                  >
                    <option value="supreme_court">Supreme Court of India</option>
                    <option value="high_court">High Court of a State / UT</option>
                    <option value="district_court">District &amp; Sessions Court</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider mb-1">
                    Court Name &amp; Bench
                  </label>
                  <input
                    type="text"
                    value={formData.court_name}
                    onChange={(e) => setFormData({ ...formData, court_name: e.target.value })}
                    className="w-full bg-white border-2 border-slate-300 rounded-xl px-3.5 py-2 text-sm font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#071e17]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider mb-1">
                    State / Union Territory
                  </label>
                  <input
                    type="text"
                    value={formData.state_ut || ""}
                    onChange={(e) => setFormData({ ...formData, state_ut: e.target.value })}
                    placeholder="e.g. Delhi, Maharashtra, Karnataka"
                    className="w-full bg-white border-2 border-slate-300 rounded-xl px-3.5 py-2 text-sm font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#071e17]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider mb-1">
                    Jurisdiction Category
                  </label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value as any })}
                    className="w-full bg-white border-2 border-slate-300 rounded-xl px-3.5 py-2 text-sm font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#071e17]"
                  >
                    <option value="constitutional">Constitutional Original</option>
                    <option value="criminal">Criminal Jurisdiction</option>
                    <option value="civil">Civil Jurisdiction</option>
                    <option value="special_leave">Special Leave / Appellate</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider mb-1">
                    Case Number (if allotted)
                  </label>
                  <input
                    type="text"
                    value={formData.case_number || ""}
                    onChange={(e) => setFormData({ ...formData, case_number: e.target.value })}
                    placeholder="e.g. WP (C) No. ___ / 2026"
                    className="w-full bg-white border-2 border-slate-300 rounded-xl px-3.5 py-2 text-sm font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#071e17]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider mb-1">
                  Applicable Statutory Provisions
                </label>
                <input
                  type="text"
                  value={formData.statutory_provisions || ""}
                  onChange={(e) => setFormData({ ...formData, statutory_provisions: e.target.value })}
                  placeholder="e.g. Article 32 of Constitution / Section 439 CrPC / Section 483 BNSS"
                  className="w-full bg-white border-2 border-slate-300 rounded-xl px-3.5 py-2 text-sm font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#071e17]"
                />
              </div>
            </div>
          )}

          {/* STEP 2: Parties & Advocates */}
          {wizardStep === 2 && (
            <div className="bg-white border-2 border-slate-200 rounded-2xl p-6 shadow-xs space-y-6">
              {/* Petitioners List */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-base text-slate-950 flex items-center space-x-2">
                    <Users className="h-4 w-4 text-[#071e17]" />
                    <span>Petitioner(s) / Applicant(s)</span>
                  </h4>
                  <button
                    type="button"
                    onClick={() =>
                      setFormData({
                        ...formData,
                        petitioners: [
                          ...formData.petitioners,
                          {
                            name: "",
                            age: "",
                            relation: "",
                            address: "",
                            role: `Petitioner No. ${formData.petitioners.length + 1}`,
                          },
                        ],
                      })
                    }
                    className="text-xs font-bold text-[#071e17] bg-[#edf2ec] border border-[#c2d4c0] px-3 py-1 rounded-lg hover:bg-slate-200"
                  >
                    + Add Co-Petitioner
                  </button>
                </div>

                {formData.petitioners.map((pet, pIdx) => (
                  <div key={pIdx} className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3">
                    <div className="flex items-center justify-between text-xs font-bold text-slate-800">
                      <span>Party #{pIdx + 1} ({pet.role})</span>
                      {formData.petitioners.length > 1 && (
                        <button
                          type="button"
                          onClick={() =>
                            setFormData({
                              ...formData,
                              petitioners: formData.petitioners.filter((_, i) => i !== pIdx),
                            })
                          }
                          className="text-rose-600 hover:text-rose-800"
                        >
                          Remove
                        </button>
                      )}
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">Name</label>
                        <input
                          type="text"
                          value={pet.name}
                          onChange={(e) => {
                            const updated = [...formData.petitioners];
                            updated[pIdx].name = e.target.value;
                            setFormData({ ...formData, petitioners: updated });
                          }}
                          placeholder="e.g. Mohan Lal"
                          className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-sm font-medium"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">Age (Years)</label>
                        <input
                          type="text"
                          value={pet.age || ""}
                          onChange={(e) => {
                            const updated = [...formData.petitioners];
                            updated[pIdx].age = e.target.value;
                            setFormData({ ...formData, petitioners: updated });
                          }}
                          placeholder="e.g. 48"
                          className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-sm font-medium"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">Parentage / Relation</label>
                        <input
                          type="text"
                          value={pet.relation || ""}
                          onChange={(e) => {
                            const updated = [...formData.petitioners];
                            updated[pIdx].relation = e.target.value;
                            setFormData({ ...formData, petitioners: updated });
                          }}
                          placeholder="e.g. S/o Late Shri Ram Lal"
                          className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-sm font-medium"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">Complete Residential Address</label>
                      <input
                        type="text"
                        value={pet.address}
                        onChange={(e) => {
                          const updated = [...formData.petitioners];
                          updated[pIdx].address = e.target.value;
                          setFormData({ ...formData, petitioners: updated });
                        }}
                        placeholder="House / Flat No., Street, City, State, PIN"
                        className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-sm font-medium"
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Respondents List */}
              <div className="space-y-3 pt-3 border-t border-slate-200">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-base text-slate-950 flex items-center space-x-2">
                    <Users className="h-4 w-4 text-[#071e17]" />
                    <span>Respondent(s)</span>
                  </h4>
                  <button
                    type="button"
                    onClick={() =>
                      setFormData({
                        ...formData,
                        respondents: [
                          ...formData.respondents,
                          {
                            name: "",
                            address: "",
                            role: `Respondent No. ${formData.respondents.length + 1}`,
                          },
                        ],
                      })
                    }
                    className="text-xs font-bold text-[#071e17] bg-[#edf2ec] border border-[#c2d4c0] px-3 py-1 rounded-lg hover:bg-slate-200"
                  >
                    + Add Respondent
                  </button>
                </div>

                {formData.respondents.map((resp, rIdx) => (
                  <div key={rIdx} className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3">
                    <div className="flex items-center justify-between text-xs font-bold text-slate-800">
                      <span>Respondent #{rIdx + 1} ({resp.role})</span>
                      {formData.respondents.length > 1 && (
                        <button
                          type="button"
                          onClick={() =>
                            setFormData({
                              ...formData,
                              respondents: formData.respondents.filter((_, i) => i !== rIdx),
                            })
                          }
                          className="text-rose-600 hover:text-rose-800"
                        >
                          Remove
                        </button>
                      )}
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">Respondent Name / Authority</label>
                        <input
                          type="text"
                          value={resp.name}
                          onChange={(e) => {
                            const updated = [...formData.respondents];
                            updated[rIdx].name = e.target.value;
                            setFormData({ ...formData, respondents: updated });
                          }}
                          placeholder="e.g. State of NCT of Delhi / Municipal Corporation"
                          className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-sm font-medium"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">Official Office Address</label>
                        <input
                          type="text"
                          value={resp.address}
                          onChange={(e) => {
                            const updated = [...formData.respondents];
                            updated[rIdx].address = e.target.value;
                            setFormData({ ...formData, respondents: updated });
                          }}
                          placeholder="e.g. Through Commissioner / SHO, Civic Centre, New Delhi"
                          className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-sm font-medium"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* STEP 3: Facts & Chronology */}
          {wizardStep === 3 && (
            <div className="bg-white border-2 border-slate-200 rounded-2xl p-6 shadow-xs space-y-5">
              <div>
                <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider mb-1">
                  Dispute Narrative &amp; Background
                </label>
                <textarea
                  rows={4}
                  value={formData.dispute_background}
                  onChange={(e) => setFormData({ ...formData, dispute_background: e.target.value })}
                  placeholder="Provide an overview of the legal controversy, grievance, and cause of action..."
                  className="w-full bg-white border-2 border-slate-300 rounded-xl p-3 text-sm font-medium text-slate-900 leading-relaxed focus:outline-none focus:ring-2 focus:ring-[#071e17]"
                />
              </div>

              {/* Chronological Events */}
              <div className="space-y-3 pt-3 border-t border-slate-200">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-sm text-slate-950 flex items-center space-x-2">
                    <Calendar className="h-4 w-4 text-[#071e17]" />
                    <span>Chronological Events (List of Dates)</span>
                  </h4>
                  <button
                    type="button"
                    onClick={() =>
                      setFormData({
                        ...formData,
                        events: [...formData.events, { date: "", description: "" }],
                      })
                    }
                    className="text-xs font-bold text-[#071e17] bg-[#edf2ec] border border-[#c2d4c0] px-3 py-1 rounded-lg hover:bg-slate-200"
                  >
                    + Add Date Event
                  </button>
                </div>

                {formData.events.map((ev, eIdx) => (
                  <div key={eIdx} className="flex items-start space-x-2">
                    <input
                      type="text"
                      value={ev.date}
                      onChange={(e) => {
                        const updated = [...formData.events];
                        updated[eIdx].date = e.target.value;
                        setFormData({ ...formData, events: updated });
                      }}
                      placeholder="Date (e.g. 10.10.2026)"
                      className="w-36 bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs font-bold shrink-0"
                    />
                    <input
                      type="text"
                      value={ev.description}
                      onChange={(e) => {
                        const updated = [...formData.events];
                        updated[eIdx].description = e.target.value;
                        setFormData({ ...formData, events: updated });
                      }}
                      placeholder="Description of the occurrence or statutory notice..."
                      className="flex-1 bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs font-medium"
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setFormData({
                          ...formData,
                          events: formData.events.filter((_, i) => i !== eIdx),
                        })
                      }
                      className="p-1.5 text-rose-600 hover:text-rose-800"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>

              {/* Supporting Annexures */}
              <div className="space-y-3 pt-3 border-t border-slate-200">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-sm text-slate-950 flex items-center space-x-2">
                    <FileText className="h-4 w-4 text-[#071e17]" />
                    <span>Supporting Annexures / Exhibits</span>
                  </h4>
                  <button
                    type="button"
                    onClick={() =>
                      setFormData({
                        ...formData,
                        annexures: [
                          ...formData.annexures,
                          {
                            mark: `P-${formData.annexures.length + 1}`,
                            title: "",
                            description: "",
                          },
                        ],
                      })
                    }
                    className="text-xs font-bold text-[#071e17] bg-[#edf2ec] border border-[#c2d4c0] px-3 py-1 rounded-lg hover:bg-slate-200"
                  >
                    + Add Annexure
                  </button>
                </div>

                {formData.annexures.map((ann, aIdx) => (
                  <div key={aIdx} className="flex items-start space-x-2">
                    <input
                      type="text"
                      value={ann.mark}
                      onChange={(e) => {
                        const updated = [...formData.annexures];
                        updated[aIdx].mark = e.target.value;
                        setFormData({ ...formData, annexures: updated });
                      }}
                      className="w-20 bg-white border border-slate-300 rounded-lg px-2 py-1.5 text-xs font-bold text-center shrink-0"
                    />
                    <input
                      type="text"
                      value={ann.title}
                      onChange={(e) => {
                        const updated = [...formData.annexures];
                        updated[aIdx].title = e.target.value;
                        setFormData({ ...formData, annexures: updated });
                      }}
                      placeholder="Title of document (e.g. True copy of Impugned Notice)"
                      className="flex-1 bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs font-medium"
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setFormData({
                          ...formData,
                          annexures: formData.annexures.filter((_, i) => i !== aIdx),
                        })
                      }
                      className="p-1.5 text-rose-600 hover:text-rose-800"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* STEP 4: Legal Grounds & Relief */}
          {wizardStep === 4 && (
            <div className="bg-white border-2 border-slate-200 rounded-2xl p-6 shadow-xs space-y-5">
              {/* Grounds of Law */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-sm text-slate-950">
                    Legal Grounds (Each ground will cite supporting Supreme Court precedents)
                  </h4>
                  <button
                    type="button"
                    onClick={() =>
                      setFormData({
                        ...formData,
                        grounds: [...formData.grounds, ""],
                      })
                    }
                    className="text-xs font-bold text-[#071e17] bg-[#edf2ec] border border-[#c2d4c0] px-3 py-1 rounded-lg hover:bg-slate-200"
                  >
                    + Add Ground
                  </button>
                </div>

                {formData.grounds.map((gText, gIdx) => (
                  <div key={gIdx} className="flex items-start space-x-2">
                    <span className="font-mono text-xs font-bold py-2 w-8 text-center text-slate-600 shrink-0">
                      {String.fromCharCode(65 + gIdx)}.
                    </span>
                    <textarea
                      rows={2}
                      value={gText}
                      onChange={(e) => {
                        const updated = [...formData.grounds];
                        updated[gIdx] = e.target.value;
                        setFormData({ ...formData, grounds: updated });
                      }}
                      placeholder="Enter legal ground of challenge..."
                      className="flex-1 bg-white border border-slate-300 rounded-lg p-2 text-xs font-medium focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setFormData({
                          ...formData,
                          grounds: formData.grounds.filter((_, i) => i !== gIdx),
                        })
                      }
                      className="p-1.5 text-rose-600 hover:text-rose-800 mt-1"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>

              {/* Main Prayers */}
              <div className="space-y-3 pt-3 border-t border-slate-200">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-sm text-slate-950">
                    Final Prayers / Reliefs Sought
                  </h4>
                  <button
                    type="button"
                    onClick={() =>
                      setFormData({
                        ...formData,
                        main_prayers: [...formData.main_prayers, ""],
                      })
                    }
                    className="text-xs font-bold text-[#071e17] bg-[#edf2ec] border border-[#c2d4c0] px-3 py-1 rounded-lg hover:bg-slate-200"
                  >
                    + Add Prayer
                  </button>
                </div>

                {formData.main_prayers.map((mp, mIdx) => (
                  <div key={mIdx} className="flex items-start space-x-2">
                    <span className="font-mono text-xs font-bold py-2 w-8 text-center text-slate-600 shrink-0">
                      ({String.fromCharCode(97 + mIdx)})
                    </span>
                    <input
                      type="text"
                      value={mp}
                      onChange={(e) => {
                        const updated = [...formData.main_prayers];
                        updated[mIdx] = e.target.value;
                        setFormData({ ...formData, main_prayers: updated });
                      }}
                      placeholder="e.g. Issue a Writ of Certiorari quashing the impugned notice..."
                      className="flex-1 bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs font-medium"
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setFormData({
                          ...formData,
                          main_prayers: formData.main_prayers.filter((_, i) => i !== mIdx),
                        })
                      }
                      className="p-1.5 text-rose-600 hover:text-rose-800"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>

              {/* Interim Relief */}
              <div className="space-y-3 pt-3 border-t border-slate-200">
                <h4 className="font-bold text-sm text-slate-950">
                  Interim Relief / Ex-Parte Stay Prayer
                </h4>
                {formData.interim_prayers.map((ip, iIdx) => (
                  <div key={iIdx} className="flex items-start space-x-2">
                    <input
                      type="text"
                      value={ip}
                      onChange={(e) => {
                        const updated = [...formData.interim_prayers];
                        updated[iIdx] = e.target.value;
                        setFormData({ ...formData, interim_prayers: updated });
                      }}
                      placeholder="e.g. Grant an ex-parte ad-interim stay of the impugned order..."
                      className="flex-1 bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs font-medium"
                    />
                  </div>
                ))}

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Urgency Justification for Interim Stay</label>
                  <input
                    type="text"
                    value={formData.urgency_reason || ""}
                    onChange={(e) => setFormData({ ...formData, urgency_reason: e.target.value })}
                    placeholder="e.g. Demolition threatened within 48 hours; immediate stay is imperative to avert irreparable harm."
                    className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs font-medium"
                  />
                </div>
              </div>
            </div>
          )}

          {/* STEP 5: Review & Generate */}
          {wizardStep === 5 && (
            <div className="bg-white border-2 border-slate-200 rounded-2xl p-6 shadow-xs space-y-6">
              <div className="border-b border-slate-200 pb-3">
                <h4 className="font-bold text-lg text-slate-950">
                  Pleading Verification &amp; Drafting Summary
                </h4>
                <p className="text-xs text-slate-600 font-medium mt-0.5">
                  Confirm the structured pleading parameters before invoking the citation-grounded drafting engine.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-medium text-slate-800">
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
                  <div className="font-bold text-slate-950">Document Type &amp; Jurisdiction</div>
                  <div>Type: <b className="capitalize">{formData.petition_type.replace("_", " ")}</b></div>
                  <div>Court: <b>{formData.court_name}</b></div>
                  <div>Category: <b className="capitalize">{formData.category}</b></div>
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
                  <div className="font-bold text-slate-950">Parties Memo</div>
                  <div>Petitioner: <b>{formData.petitioners[0]?.name || "Not specified"}</b></div>
                  <div>Respondent: <b>{formData.respondents[0]?.name || "Not specified"}</b></div>
                  <div>Events Count: <b>{formData.events.length} chronological milestones</b></div>
                </div>
              </div>

              <div className="p-4 bg-[#edf2ec] border border-[#c2d4c0] rounded-xl space-y-2 text-xs">
                <div className="font-bold text-[#14532d] flex items-center space-x-1.5">
                  <CheckCircle2 className="h-4 w-4 text-[#15803d]" />
                  <span>Integrated Citation Retrieval Ready</span>
                </div>
                <p className="text-slate-800 font-medium">
                  The drafting engine will automatically search the local Supreme Court corpus for binding
                  procedural precedents supporting your grounds, extract verified paragraph references,
                  and assemble complete Cause Titles, Prayers, and Verification Affidavits.
                </p>
              </div>

              <div className="p-3.5 bg-[#faeae1] border border-[#f3d3be] rounded-xl text-xs text-[#78350f] space-y-1">
                <div className="font-bold flex items-center space-x-1.5">
                  <AlertTriangle className="h-4 w-4 text-[#b45309]" />
                  <span>Mandatory Professional Disclaimer</span>
                </div>
                <p>
                  Needhi generates informational court drafts. Under Bar Council of India guidelines,
                  all legal petitions must be independently scrutinized, finalized, and executed by an
                  enrolled advocate before filing in any court.
                </p>
              </div>
            </div>
          )}

          {/* Wizard Controls Footer */}
          <div className="flex items-center justify-between pt-2">
            {wizardStep > 1 ? (
              <button
                type="button"
                onClick={() => setWizardStep(wizardStep - 1)}
                className="flex items-center space-x-2 px-5 py-2 rounded-xl bg-white border border-slate-300 text-slate-800 text-xs sm:text-sm font-bold hover:bg-slate-50"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Previous Step</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={() => {
                  if (window.confirm("Clear all form fields and start over?")) {
                    setFormData(INITIAL_FORM_DATA);
                  }
                }}
                className="text-xs font-bold text-slate-500 hover:text-slate-800 flex items-center space-x-1"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Reset Form</span>
              </button>
            )}

            {wizardStep < 5 ? (
              <button
                type="button"
                onClick={() => setWizardStep(wizardStep + 1)}
                className="flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-[#071e17] hover:bg-[#0f2c24] text-white text-xs sm:text-sm font-bold shadow-sm"
              >
                <span>Continue</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleGenerate}
                disabled={generating}
                className="flex items-center space-x-2 px-7 py-3 rounded-xl bg-[#071e17] hover:bg-[#0f2c24] text-white text-sm font-bold shadow-md hover:shadow-lg disabled:opacity-60 cursor-pointer"
              >
                {generating ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span>Synthesizing Legal Petition...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    <span>Generate Petition Draft</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      )}

      {/* ========================================================
          VIEW 3: EDITABLE WORKSPACE & EDITOR
          ======================================================== */}
      {view === "editor" && generatedDoc && (
        <div className="space-y-6">
          {/* Top Action & Export Bar */}
          <div className="bg-white border-2 border-slate-200 rounded-2xl p-4 sm:p-5 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center space-x-2.5">
                <button
                  type="button"
                  onClick={() => setView("landing")}
                  className="text-xs font-bold text-slate-600 hover:text-slate-950 flex items-center space-x-1 pr-2 border-r border-slate-200"
                >
                  <ArrowLeft className="h-3.5 w-3.5" />
                  <span>Dashboard</span>
                </button>
                <h3 className="font-bold text-base sm:text-lg text-slate-950">
                  {generatedDoc.title}
                </h3>
                <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-300">
                  {generatedDoc.status}
                </span>
              </div>
              <p className="text-xs font-medium text-slate-600">
                {generatedDoc.court_name} &bull; Grounded with {generatedDoc.citations.length} verified precedents
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={handleSaveDraft}
                className="px-3.5 py-2 text-xs font-bold text-slate-800 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 transition-colors"
              >
                Save Draft
              </button>

              <button
                type="button"
                onClick={handleCopyFull}
                className="px-3.5 py-2 text-xs font-bold text-slate-800 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 transition-colors flex items-center space-x-1.5"
              >
                {copiedDoc ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5 text-slate-500" />}
                <span>{copiedDoc ? "Copied" : "Copy All"}</span>
              </button>

              <button
                type="button"
                onClick={handleDownloadDocx}
                className="px-4 py-2 text-xs font-bold text-white bg-[#071e17] hover:bg-[#0f2c24] rounded-xl shadow-xs transition-colors flex items-center space-x-1.5 cursor-pointer"
                title="Download real court-formatted Word document (.docx)"
              >
                <Download className="h-3.5 w-3.5 stroke-[2.5]" />
                <span>Export DOCX</span>
              </button>

              <button
                type="button"
                onClick={handleDownloadPdf}
                className="px-4 py-2 text-xs font-bold text-white bg-[#071e17] hover:bg-[#0f2c24] rounded-xl shadow-xs transition-colors flex items-center space-x-1.5 cursor-pointer"
                title="Download genuine printable legal PDF (.pdf)"
              >
                <Download className="h-3.5 w-3.5 stroke-[2.5]" />
                <span>Export PDF</span>
              </button>
            </div>
          </div>

          {/* Success Banner */}
          {saveSuccessMsg && (
            <div className="bg-emerald-50 border border-emerald-300 text-emerald-950 px-4 py-2.5 rounded-xl text-xs font-bold flex items-center space-x-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              <span>{saveSuccessMsg}</span>
            </div>
          )}

          {/* Main 3-Column Workspace */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left Column: Sections Outline (3 cols) */}
            <div className="lg:col-span-3 bg-white border-2 border-slate-200 rounded-2xl p-4 shadow-xs space-y-4">
              <div className="pb-2 border-b border-slate-200">
                <h4 className="font-bold text-sm text-slate-950">
                  Document Sections
                </h4>
                <p className="text-[11px] text-slate-600 font-medium">
                  Click a section to inspect or revise
                </p>
              </div>

              <div className="space-y-1">
                {Object.keys(editedSections).map((secKey) => {
                  const isActive = activeSectionKey === secKey;
                  const label = secKey.replace(/_/g, " ").toUpperCase();
                  return (
                    <button
                      key={secKey}
                      type="button"
                      onClick={() => setActiveSectionKey(secKey)}
                      className={`w-full text-left px-3 py-2 rounded-xl text-xs font-bold transition-colors ${
                        isActive
                          ? "bg-[#071e17] text-white shadow-xs"
                          : "text-slate-800 hover:bg-slate-100"
                      }`}
                    >
                      {label}
                    </button>
                  );
                })}
              </div>

              {/* Missing Details / Warnings Checklist */}
              {generatedDoc.verification_warnings.length > 0 && (
                <div className="pt-3 border-t border-slate-200 space-y-2">
                  <div className="text-xs font-bold text-[#78350f] flex items-center space-x-1">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    <span>Filing Verification Checklist</span>
                  </div>
                  <div className="space-y-1.5">
                    {generatedDoc.verification_warnings.map((w, idx) => (
                      <div
                        key={idx}
                        className="text-[11px] font-medium text-slate-700 bg-[#faeae1] p-2 rounded-lg border border-[#f3d3be] leading-tight"
                      >
                        {w}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Center Column: Section Editor (6 cols) */}
            <div className="lg:col-span-6 bg-white border-2 border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                <div>
                  <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                    Editing Section
                  </span>
                  <h4 className="font-bold text-base text-slate-950 uppercase">
                    {activeSectionKey.replace(/_/g, " ")}
                  </h4>
                </div>

                <button
                  type="button"
                  onClick={() => setShowRegenModal(true)}
                  className="flex items-center space-x-1.5 px-3 py-1.5 bg-[#edf2ec] hover:bg-[#dde9dc] text-[#14532d] border border-[#c2d4c0] rounded-xl text-xs font-bold transition-colors cursor-pointer"
                  title="Regenerate only this section with custom instruction"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  <span>Regenerate Section</span>
                </button>
              </div>

              {/* Editable Text Area */}
              <div>
                <textarea
                  rows={18}
                  value={editedSections[activeSectionKey] || ""}
                  onChange={(e) =>
                    setEditedSections({
                      ...editedSections,
                      [activeSectionKey]: e.target.value,
                    })
                  }
                  className="w-full bg-[#f8fafc] border border-slate-300 rounded-xl p-4 text-sm font-medium text-slate-950 leading-relaxed font-mono focus:outline-none focus:ring-2 focus:ring-[#071e17]"
                />
              </div>

              <div className="flex items-center justify-between pt-2 text-xs font-bold text-slate-600">
                <span>{editedSections[activeSectionKey]?.length || 0} characters</span>
                <span className="text-[#15803d]">Live inline editor active &bull; Edits preserved</span>
              </div>
            </div>

            {/* Right Column: Supporting Precedents & Citations (3 cols) */}
            <div className="lg:col-span-3 space-y-4">
              <div className="bg-white border-2 border-slate-200 rounded-2xl p-4 shadow-xs space-y-3">
                <div className="pb-2 border-b border-slate-200 flex items-center justify-between">
                  <h4 className="font-bold text-sm text-slate-950 flex items-center space-x-1.5">
                    <BookOpen className="h-4 w-4 text-[#071e17]" />
                    <span>Grounded Precedents ({generatedDoc.citations.length})</span>
                  </h4>
                  <span className="text-[11px] font-bold text-[#15803d] bg-[#dcfce7] border border-[#86efac] px-2 py-0.5 rounded-full">
                    Verified
                  </span>
                </div>

                <div className="space-y-3">
                  {generatedDoc.citations.map((cite) => (
                    <div
                      key={cite.marker}
                      className="p-3 rounded-xl bg-[#f8fafc] border border-slate-200 space-y-2 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-amber-950 bg-[#faeae1] border border-[#f3d3be] px-2 py-0.5 rounded">
                          {cite.marker}
                        </span>
                        {cite.para_no && (
                          <span className="text-[11px] font-bold text-slate-600">
                            Para {cite.para_no}
                          </span>
                        )}
                      </div>

                      <div className="font-bold text-slate-950 leading-snug">
                        {cite.title}
                      </div>

                      <div className="text-[11px] font-semibold text-slate-600">
                        {cite.court} &bull; {cite.neutral_citation}
                      </div>

                      <p className="text-[11px] font-medium text-slate-800 bg-white p-2 rounded border border-slate-200 italic leading-relaxed">
                        &ldquo;{cite.snippet}&rdquo;
                      </p>

                      {cite.document_id && onNavigateToCase && (
                        <button
                          type="button"
                          onClick={() => onNavigateToCase(cite.document_id || 1, cite.para_no)}
                          className="text-[11px] font-bold text-[#071e17] hover:underline flex items-center space-x-1 pt-1"
                        >
                          <span>Open in Case Viewer</span>
                          <ExternalLink className="h-3 w-3" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Legal Disclaimer Box */}
              <div className="bg-[#faeae1] border border-[#f3d3be] rounded-2xl p-4 text-xs text-[#78350f] space-y-1.5">
                <div className="font-bold flex items-center space-x-1.5">
                  <Info className="h-4 w-4 text-[#b45309]" />
                  <span>Advocate Scrutiny Standard</span>
                </div>
                <p className="leading-relaxed font-normal">
                  Needhi generates informational pleading drafts grounded in verified citations.
                  Always verify statutory provisions and cause-of-action dates against the official court Gazette.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================
          MODAL: SECTION REGENERATION
          ======================================================== */}
      {showRegenModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white border-2 border-slate-300 rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <h3 className="font-bold text-base text-slate-950">
                Regenerate &apos;{activeSectionKey.replace(/_/g, " ")}&apos;
              </h3>
              <button
                type="button"
                onClick={() => setShowRegenModal(false)}
                className="text-slate-500 hover:text-slate-800 text-sm font-bold"
              >
                &times;
              </button>
            </div>

            <p className="text-xs text-slate-700 font-medium">
              Provide specific drafting instructions for this section. All other sections of your
              petition draft will remain untouched.
            </p>

            <div>
              <label className="block text-xs font-bold text-slate-900 uppercase mb-1">
                Custom Drafting Instruction
              </label>
              <textarea
                rows={3}
                value={regenInstruction}
                onChange={(e) => setRegenInstruction(e.target.value)}
                placeholder="e.g. Emphasize parity with co-accused / Add citation to Article 14 arbitrary state action test..."
                className="w-full bg-[#f8fafc] border border-slate-300 rounded-xl p-3 text-xs font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#071e17]"
              />
            </div>

            <div className="flex items-center justify-end space-x-2.5 pt-2">
              <button
                type="button"
                onClick={() => setShowRegenModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-100 border border-slate-300"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleRegenerateCurrentSection}
                disabled={regenerating}
                className="px-5 py-2 rounded-xl text-xs font-bold text-white bg-[#071e17] hover:bg-[#0f2c24] flex items-center space-x-1.5 disabled:opacity-60 cursor-pointer"
              >
                {regenerating ? (
                  <>
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    <span>Regenerating Section...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-3.5 w-3.5" />
                    <span>Apply &amp; Regenerate</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PetitionGeneratorPage;
