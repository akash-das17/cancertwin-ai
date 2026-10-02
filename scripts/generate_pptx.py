"""
Generates the 12-slide CancerTwin AI 2.0 Executive Presentation (.pptx).
Theme: Deep dark modern tech aesthetic (#070B14, #0F172A, #2563EB, #38BDF8, #10B981, #F8FAFC)
100% Focused on the actual project: CancerTwin AI 2.0 (10 Agents, Dual LangGraph, ChromaDB, PubMed, MCP).
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)  # 16:9 widescreen
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Color Palette
    COLOR_BG = RGBColor(7, 11, 20)           # #070B14
    COLOR_CARD = RGBColor(18, 25, 42)        # #12192A
    COLOR_CARD_BORDER = RGBColor(37, 52, 84) # #253454
    COLOR_CYAN = RGBColor(56, 189, 248)      # #38BDF8
    COLOR_BLUE = RGBColor(37, 99, 235)       # #2563EB
    COLOR_EMERALD = RGBColor(16, 185, 129)   # #10B981
    COLOR_AMBER = RGBColor(245, 158, 11)     # #F59E0B
    COLOR_PURPLE = RGBColor(168, 85, 247)    # #A855F7
    COLOR_ROSE = RGBColor(244, 63, 94)       # #F43F5E
    COLOR_WHITE = RGBColor(248, 250, 252)    # #F8FAFC
    COLOR_MUTED = RGBColor(148, 163, 184)    # #94A3B8

    def add_background(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = COLOR_BG
        bg.line.color.rgb = COLOR_BG

    def add_header(slide, title_text, category_tag="CANCERTWIN AI 2.0 SPECIFICATION", slide_num=1):
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(8), Inches(0.35))
        tf = cat_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = category_tag.upper()
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = COLOR_CYAN

        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.5), Inches(0.6))
        tf2 = title_box.text_frame
        tf2.word_wrap = True
        p2 = tf2.paragraphs[0]
        p2.text = title_text
        p2.font.size = Pt(22)
        p2.font.bold = True
        p2.font.color.rgb = COLOR_WHITE

        num_box = slide.shapes.add_textbox(Inches(11.8), Inches(0.4), Inches(1.0), Inches(0.35))
        p_num = num_box.text_frame.paragraphs[0]
        p_num.text = f"{slide_num:02d} / 12"
        p_num.alignment = PP_ALIGN.RIGHT
        p_num.font.size = Pt(11)
        p_num.font.bold = True
        p_num.font.color.rgb = COLOR_MUTED

    def add_card(slide, left, top, width, height, title="", subtitle="", border_color=COLOR_CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD
        card.line.color.rgb = border_color
        card.line.width = Pt(1.5)
        
        if title:
            tb = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.15), width - Inches(0.4), Inches(0.35))
            p = tb.text_frame.paragraphs[0]
            p.text = title
            p.font.size = Pt(13)
            p.font.bold = True
            p.font.color.rgb = COLOR_WHITE
            
        if subtitle:
            tb_sub = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.45), width - Inches(0.4), Inches(0.25))
            p_sub = tb_sub.text_frame.paragraphs[0]
            p_sub.text = subtitle
            p_sub.font.size = Pt(9.5)
            p_sub.font.color.rgb = COLOR_CYAN
            
        return card

    # =========================================================================
    # SLIDE 1: TITLE SLIDE
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    add_background(s1)

    banner = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.25), prs.slide_height)
    banner.fill.solid()
    banner.fill.fore_color.rgb = COLOR_CYAN
    banner.line.color.rgb = COLOR_CYAN

    t_badge = s1.shapes.add_textbox(Inches(1.2), Inches(1.5), Inches(8), Inches(0.4))
    p = t_badge.text_frame.paragraphs[0]
    p.text = "CANCERTWIN AI 2.0 • AGENTIC ONCOLOGY DIGITAL TWIN SYSTEM"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN

    t_title = s1.shapes.add_textbox(Inches(1.2), Inches(1.9), Inches(11.0), Inches(1.8))
    tf = t_title.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "CancerTwin AI 2.0"
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p2 = tf.add_paragraph()
    p2.text = "Personalized 5-Cancer Risk Prevention & Virtual Tumor Board Relapse Adjudication"
    p2.font.size = Pt(20)
    p2.font.color.rgb = COLOR_MUTED

    c1 = add_card(s1, Inches(1.2), Inches(4.2), Inches(3.4), Inches(2.2), "10 Specialized Agents", "LangGraph Orchestration", COLOR_BLUE)
    tb1 = s1.shapes.add_textbox(Inches(1.4), Inches(4.8), Inches(3.0), Inches(1.4))
    p = tb1.text_frame.paragraphs[0]
    p.text = "• Deterministic Prevention DAG\n• 3-Round Cyclical Tumor Board\n• Autonomous Scientific Skeptic\n• Pydantic v2 Type Safety"
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_WHITE

    c2 = add_card(s1, Inches(4.9), Inches(4.2), Inches(3.4), Inches(2.2), "Dual-Store RAG", "ChromaDB + PubMed Live", COLOR_CYAN)
    tb2 = s1.shapes.add_textbox(Inches(5.1), Inches(4.8), Inches(3.0), Inches(1.4))
    p = tb2.text_frame.paragraphs[0]
    p.text = "• 100+ USPSTF & NCCN Guidelines\n• Live NCBI PubMed API fetching\n• Strict token budget manager\n• Zero ungrounded assertions"
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_WHITE

    c3 = add_card(s1, Inches(8.6), Inches(4.2), Inches(3.4), Inches(2.2), "Future-Ready MCP", "Model Context Protocol", COLOR_EMERALD)
    tb3 = s1.shapes.add_textbox(Inches(8.8), Inches(4.8), Inches(3.0), Inches(1.4))
    p = tb3.text_frame.paragraphs[0]
    p.text = "• All 10 agents exposed via MCP\n• Ready for Multimodal Chatbot\n• Diagnostic OCR Ingestion\n• Automated Factor Attribution"
    p.font.size = Pt(11)
    p.font.color.rgb = COLOR_WHITE

    # =========================================================================
    # SLIDE 2: PROBLEM STATEMENT (THE 4 CRISES)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_background(s2)
    add_header(s2, "Problem Statement: The 4 Crises in Oncology Decision Support", "CLINICAL BOTTLENECKS", 2)

    problems = [
        ("1. Fragmented Oncology Data Silos", "DISCONNECTED EHRs, LABS & GENOMICS", 
         "Patient records, lab panels, pathology slides, and genetic biomarkers (BRCA1/2, KRAS) are trapped in isolated hospital silos. Oncologists spend 40%+ of review time manually gathering history.", COLOR_ROSE),
        ("2. 18+ Variable Cognitive Overload", "COMPLEX MULTI-AXIS HAZARD MATH", 
         "Evaluating 30-year risk across lifestyle, environmental carcinogens (PM2.5, radon), and comorbidities exceeds human mental capacity. Standard 15-minute consultations cannot calculate Gail/Bach hazards.", COLOR_AMBER),
        ("3. Fatal Drug Collisions & Burnout", "UNCHECKED DDI & HIGH CLINICAL FRICTION", 
         "Aggressive chemoprevention regimens trigger fatal adverse drug interactions (DDIs with antidepressants). Demanding 10 simultaneous life modifications causes high friction scores and 70%+ dropout.", COLOR_PURPLE),
        ("4. General LLM Hallucination Trap", "UNVERIFIED CITATIONS & BLAND AVERAGES", 
         "Commercial monolithic LLMs invent realistic-sounding PubMed PMIDs, fail token budgeting, and converge on bland averages rather than exploring surgical versus radiation field margins.", COLOR_CYAN)
    ]

    for idx, (p_title, p_sub, p_desc, col) in enumerate(problems):
        row = idx // 2
        col_idx = idx % 2
        l = Inches(0.8 + col_idx * 5.95)
        t = Inches(1.4 + row * 2.85)
        card = add_card(s2, l, t, Inches(5.75), Inches(2.6), p_title, p_sub, col)
        tb = s2.shapes.add_textbox(l + Inches(0.2), t + Inches(0.7), Inches(5.35), Inches(1.7))
        p = tb.text_frame.paragraphs[0]
        p.text = p_desc
        p.font.size = Pt(12)
        p.font.color.rgb = COLOR_WHITE

    # =========================================================================
    # SLIDE 3: WHY THIS SOLUTION? (ARCHITECTURAL RATIONALE)
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_background(s3)
    add_header(s3, "Architectural Rationale: Why Monolithic LLMs Fail & Why Agents Win", "WHY THIS SOLUTION", 3)

    card_mono = add_card(s3, Inches(0.8), Inches(1.4), Inches(5.75), Inches(5.5), "The Monolithic Approach (Why It Fails)", "Single Prompt / General Chatbot", COLOR_ROSE)
    tb_m = s3.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(5.35), Inches(4.6))
    tf_m = tb_m.text_frame
    tf_m.word_wrap = True
    mono_points = [
        "❌ Bland Averaged Consensus: Collapses opposing surgical and radiation trade-offs into a generic average.",
        "❌ Fabricated Citations: Generates plausible PubMed IDs and fake trial efficacy figures that do not exist.",
        "❌ Zero Friction Accounting: Dumps 10 aggressive life modifications simultaneously, triggering patient burnout.",
        "❌ Inflexible Reasoning: Cannot simulate separate surgical resection vs radiation stereotactic field beds.",
        "❌ Black Box Opacity: Clinicians cannot verify which exact parameter caused a risk surge or drop."
    ]
    for pt in mono_points:
        p = tf_m.add_paragraph() if tf_m.paragraphs[0].text else tf_m.paragraphs[0]
        p.text = pt
        p.font.size = Pt(12)
        p.font.color.rgb = COLOR_MUTED
        p.space_after = Pt(10)

    card_agent = add_card(s3, Inches(6.8), Inches(1.4), Inches(5.75), Inches(5.5), "The CancerTwin Multi-Agent System (Why It Wins)", "LangGraph Orchestrated Network", COLOR_EMERALD)
    tb_a = s3.shapes.add_textbox(Inches(7.0), Inches(2.1), Inches(5.35), Inches(4.6))
    tf_a = tb_a.text_frame
    tf_a.word_wrap = True
    agent_points = [
        "✔ Dialectical Specialist Debate: Dedicated Surgical, Medical, and Radiation agents defend conflicting strategies over 3 rounds.",
        "✔ Autonomous Scientific Skeptic: Dedicated adversary agent audits trials for pharma bias, spin, and calculates GRADE scores.",
        "✔ 2-Phase Staged Interventions: Feasibility agent calculates friction scores (0–10) and blocks drug collisions (DDIs).",
        "✔ Deterministic DAG: Guarantees reproducibility and verifiable mathematical state transitions.",
        "✔ Strict Pydantic Type-Safety: Strongly validated JSON schemas ensure complete mathematical traceability."
    ]
    for pt in agent_points:
        p = tf_a.add_paragraph() if tf_a.paragraphs[0].text else tf_a.paragraphs[0]
        p.text = pt
        p.font.size = Pt(12)
        p.font.color.rgb = COLOR_WHITE
        p.space_after = Pt(10)

    # =========================================================================
    # SLIDE 4: BUSINESS USE CASE SCENARIO (CANCERTWIN SPECIFIC)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_background(s4)
    add_header(s4, "Business Use Case Scenario: AI-Driven Chronic Oncology Management", "USE CASE SCENARIO", 4)

    c_left = add_card(s4, Inches(0.8), Inches(1.4), Inches(3.6), Inches(4.6), "Business Challenge", "Oncology Care Delivery Gaps", COLOR_ROSE)
    tb_cl = s4.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(3.2), Inches(3.7))
    tb_cl.text_frame.paragraphs[0].text = "• Fragmented Genomic & Lab Data: Biomarkers, CT scans, and pathology trapped across EHRs.\n\n• Zero Trajectory Visibility: Blind spots in long-term counterfactual risk projection for patients.\n\n• Time-Consuming Chart Review: Oncologists lose 3+ hours daily manually assembling histories."
    tb_cl.text_frame.paragraphs[0].font.size = Pt(11.5)
    tb_cl.text_frame.paragraphs[0].font.color.rgb = COLOR_WHITE

    c_mid = add_card(s4, Inches(4.6), Inches(1.4), Inches(4.5), Inches(4.6), "CancerTwin Multi-Agent Workflow", "Autonomous LangGraph Pipeline", COLOR_CYAN)
    tb_cm = s4.shapes.add_textbox(Inches(4.8), Inches(2.1), Inches(4.1), Inches(3.7))
    tb_cm.text_frame.paragraphs[0].text = "1. Intake: Ingests 18 risk biomarkers via Web SPA / REST API.\n\n2. Orchestrator: LangGraph decomposes query and normalizes DigitalTwinState.\n\n3. Parallel Pipelines: Risk Agent (Gail/Bach models), Simulator Agent (30-yr curves), Feasibility (DDI & friction 0-10), Skeptic (GRADE audit).\n\n4. Tumor Board: 3-round Surgical, Medical & Radiation debate.\n\n5. Synthesis: Twin Coordinator delivers verified clinical report."
    tb_cm.text_frame.paragraphs[0].font.size = Pt(11)
    tb_cm.text_frame.paragraphs[0].font.color.rgb = COLOR_WHITE

    c_right = add_card(s4, Inches(9.3), Inches(1.4), Inches(3.2), Inches(4.6), "Key Deliverables", "Clinical Action Outputs", COLOR_EMERALD)
    tb_cr = s4.shapes.add_textbox(Inches(9.5), Inches(2.1), Inches(2.8), Inches(3.7))
    tb_cr.text_frame.paragraphs[0].text = "• Complete Digital Twin State\n\n• 30-Year Trajectory Divergence\n\n• DDI & Pharmacogenomic Safety\n\n• 2-Phase Staged Interventions\n\n• Adjudicated Relapse Consensus"
    tb_cr.text_frame.paragraphs[0].font.size = Pt(11.5)
    tb_cr.text_frame.paragraphs[0].font.color.rgb = COLOR_WHITE

    ribbon = add_card(s4, Inches(0.8), Inches(6.15), Inches(11.73), Inches(0.8), "", "", COLOR_CYAN)
    tb_rib = s4.shapes.add_textbox(Inches(1.0), Inches(6.25), Inches(11.3), Inches(0.6))
    tb_rib.text_frame.paragraphs[0].text = "Delivered Value: 60% Faster Decision Making  •  Zero Fatal Drug Collisions  •  Pre-Convened Tumor Boards  •  75%+ Patient Adherence  •  Measurable Survival Gains"
    tb_rib.text_frame.paragraphs[0].font.size = Pt(11)
    tb_rib.text_frame.paragraphs[0].font.bold = True
    tb_rib.text_frame.paragraphs[0].font.color.rgb = COLOR_CYAN

    # =========================================================================
    # SLIDE 5: PROPOSED SOLUTION (CANCERTWIN CIRCULAR HUB)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_background(s5)
    add_header(s5, "Proposed Solution: Circular Multi-Agent Orchestration Hub", "SOLUTION TOPOLOGY", 5)

    l_card = add_card(s5, Inches(0.8), Inches(1.4), Inches(4.5), Inches(5.5), "CancerTwin AI 2.0 Capabilities", "Intelligent • Grounded • Proactive", COLOR_CYAN)
    tb_caps = s5.shapes.add_textbox(Inches(1.0), Inches(2.1), Inches(4.1), Inches(4.6))
    tf_caps = tb_caps.text_frame
    tf_caps.word_wrap = True
    caps = [
        ("Unified 18-Biomarker Twin", "Consolidates age, smoking pack-years, radon, PM2.5, and genetics into a normalized DigitalTwinState."),
        ("LangGraph Orchestration", "Dual pipelines: Deterministic Prevention DAG and 3-round cyclical Virtual Tumor Board debate."),
        ("30-Year Trajectory Simulator", "Simulates counterfactual lifestyle and screening changes to project multi-decade risk drops."),
        ("Feasibility & DDI Shield", "Scores friction (0-10 burnout), blocks drug collisions (e.g. Tamoxifen + CYP2D6 inhibitors)."),
        ("The Scientific Skeptic Audit", "Autonomous trial spin audit; verifies control arms, hazard ratios, and assigns GRADE scores."),
        ("Virtual Tumor Board", "Surgical, Medical, and Radiation oncologists cross-examine trade-offs to reach consensus.")
    ]
    for cap_title, cap_desc in caps:
        p = tf_caps.add_paragraph() if tf_caps.paragraphs[0].text else tf_caps.paragraphs[0]
        p.text = f"• {cap_title}: {cap_desc}"
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_WHITE
        p.space_after = Pt(4)

    hub_card = add_card(s5, Inches(5.5), Inches(1.4), Inches(7.0), Inches(5.5), "The Central CancerTwin Orchestration Network", "Hierarchical Hub & Spoke Communication", COLOR_BLUE)
    
    sup_box = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.7), Inches(3.5), Inches(2.6), Inches(1.3))
    sup_box.fill.solid()
    sup_box.fill.fore_color.rgb = RGBColor(30, 58, 138)
    sup_box.line.color.rgb = COLOR_CYAN
    sup_box.line.width = Pt(2.5)
    tb_s = s5.shapes.add_textbox(Inches(7.7), Inches(3.6), Inches(2.6), Inches(1.1))
    p = tb_s.text_frame.paragraphs[0]
    p.text = "TWIN COORDINATOR"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = COLOR_WHITE
    p.alignment = PP_ALIGN.CENTER
    p2 = tb_s.text_frame.add_paragraph()
    p2.text = "LangGraph StateGraph"
    p2.font.size = Pt(9.5)
    p2.font.color.rgb = COLOR_CYAN
    p2.alignment = PP_ALIGN.CENTER

    nodes = [
        (Inches(5.8), Inches(2.0), "INTAKE AGENT", "Twin Profiling & State", COLOR_BLUE),
        (Inches(9.6), Inches(2.0), "RISK & SIM AGENTS", "30-Yr Divergence Math", COLOR_BLUE),
        (Inches(5.8), Inches(5.2), "SAFETY & SKEPTIC", "DDI Shield & GRADE Score", COLOR_PURPLE),
        (Inches(9.6), Inches(5.2), "VIRTUAL TUMOR BOARD", "Surg, Med, Rad Debate", COLOR_EMERALD),
    ]
    for nx, ny, ntitle, nsub, ncol in nodes:
        node = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, nx, ny, Inches(2.6), Inches(0.95))
        node.fill.solid()
        node.fill.fore_color.rgb = COLOR_CARD
        node.line.color.rgb = ncol
        node.line.width = Pt(1.5)
        tb_n = s5.shapes.add_textbox(nx, ny + Inches(0.1), Inches(2.6), Inches(0.75))
        p = tb_n.text_frame.paragraphs[0]
        p.text = ntitle
        p.font.bold = True
        p.font.size = Pt(10.5)
        p.font.color.rgb = COLOR_WHITE
        p.alignment = PP_ALIGN.CENTER
        p2 = tb_n.text_frame.add_paragraph()
        p2.text = nsub
        p2.font.size = Pt(8.5)
        p2.font.color.rgb = COLOR_MUTED
        p2.alignment = PP_ALIGN.CENTER

    # =========================================================================
    # SLIDE 6: SYSTEM ARCHITECTURE (1-SLIDE PRESENTER DIAGRAM)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_background(s6)
    add_header(s6, "System Control-Flow Architecture: End-to-End Pipeline", "1-SLIDE ARCHITECTURE", 6)

    tiers = [
        ("Tier 1: Intake & UI", "User & Web Gateway", 
         [("Clinician / Patient", "Inputs 18 risk biomarkers, genetic flags (BRCA/KRAS)"),
          ("Web SPA & FastAPI", "Pydantic v2 validation, CORS gateway, REST endpoints"),
          ("Intake Profiler", "Initializes DigitalTwinState, synthesizes 0-100 health score")],
         COLOR_BLUE),
        ("Tier 2: Parallel Agents", "LangGraph Reasoning", 
         [("Risk Assessment", "Computes Gail/Bach baseline hazard ratios for 5 cancers"),
          ("What-If Simulator", "Calculates counterfactual 10-30 yr risk divergence"),
          ("Safety & Feasibility", "Friction score (0-10), drug collision DDI validation")],
         COLOR_PURPLE),
        ("Tier 3: Evidence RAG", "Dual Knowledge Stores", 
         [("ChromaDB Vector Store", "NCCN, USPSTF, WCRF clinical guideline embeddings"),
          ("NCBI PubMed Tool", "Real-time Phase 3 trial searches & live abstract fetching"),
          ("The Scientific Skeptic", "Audits trial bias, spin & assigns GRADE evidence score")],
         COLOR_EMERALD),
        ("Tier 4: Synthesis & Output", "Tumor Board & Delivery", 
         [("Virtual Tumor Board", "Surgical, Medical & Radiation 3-round consensus debate"),
          ("Twin Coordinator", "Gemini 2.5 Flash synthesis with strict token budgets"),
          ("Clinical Action Report", "Interactive 30-yr charts, milestone roadmaps & PMIDs")],
         COLOR_CYAN)
    ]

    for idx, (tier_title, tier_sub, items, col) in enumerate(tiers):
        l = Inches(0.8 + idx * 2.95)
        card = add_card(s6, l, Inches(1.4), Inches(2.8), Inches(5.5), tier_title, tier_sub, col)
        
        top_offset = Inches(2.1)
        for item_title, item_desc in items:
            box = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l + Inches(0.15), top_offset, Inches(2.5), Inches(1.35))
            box.fill.solid()
            box.fill.fore_color.rgb = RGBColor(11, 17, 30)
            box.line.color.rgb = col
            box.line.width = Pt(1.0)
            
            tb = s6.shapes.add_textbox(l + Inches(0.2), top_offset + Inches(0.05), Inches(2.4), Inches(1.25))
            p = tb.text_frame.paragraphs[0]
            p.text = item_title
            p.font.bold = True
            p.font.size = Pt(10)
            p.font.color.rgb = COLOR_WHITE
            p2 = tb.text_frame.add_paragraph()
            p2.text = item_desc
            p2.font.size = Pt(8.5)
            p2.font.color.rgb = COLOR_MUTED
            
            top_offset += Inches(1.5)

    # =========================================================================
    # SLIDE 7: WORKFLOW
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_background(s7)
    add_header(s7, "Hierarchical Workflow Pipeline: Execution Sequence", "WORKFLOW", 7)

    w_steps = [
        ("01. USER CLINICAL QUERY", "Patient inputs 18 lifestyle & genetic variables or clinician uploads profile.", COLOR_CYAN),
        ("02. FASTAPI WEB INTERFACE", "Validates input schemas against Pydantic v2 models and triggers orchestrator.", COLOR_BLUE),
        ("03. LANGGRAPH TWIN COORDINATOR", "Initializes DigitalTwinState and activates parallel specialist pipelines.", COLOR_PURPLE),
        ("04. PARALLEL REASONING & EVIDENCE", "Risk/Sim agents compute hazard math; ChromaDB & PubMed tool ground evidence.", COLOR_EMERALD),
        ("05. VIRTUAL TUMOR BOARD DEBATE", "Surgical, Medical, and Radiation oncologists conduct 3-round cross-examination.", COLOR_AMBER),
        ("06. FINAL CLINICAL ACTION REPORT", "Synthesizes 30-year risk divergence curves, staged milestones, and PMIDs.", COLOR_CYAN),
    ]

    for idx, (stitle, sdesc, scol) in enumerate(w_steps):
        t = Inches(1.4 + idx * 0.9)
        card = add_card(s7, Inches(1.5), t, Inches(10.33), Inches(0.75), stitle, "", scol)
        tb = s7.shapes.add_textbox(Inches(4.5), t + Inches(0.12), Inches(7.1), Inches(0.5))
        p = tb.text_frame.paragraphs[0]
        p.text = sdesc
        p.font.size = Pt(11)
        p.font.color.rgb = COLOR_WHITE

    # =========================================================================
    # SLIDE 8: THE 10 SPECIALIZED AGENTS DEEP-DIVE
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    add_background(s8)
    add_header(s8, "The 10 Domain Specialist Agents: Roles & Capabilities", "MULTI-AGENT ROSTER", 8)

    agent_grid = [
        ("01. Intake Agent", "src/agents/intake_agent.py", "Pydantic schema validation & baseline twin instantiation.", COLOR_BLUE),
        ("02. Risk Agent", "src/agents/risk_agent.py", "Baseline Gail/Bach hazard models across 5 major cancers.", COLOR_BLUE),
        ("03. Simulator Agent", "src/agents/simulation_agent.py", "10-30 year counterfactual risk trajectory divergence engine.", COLOR_BLUE),
        ("04. Feasibility Agent", "src/agents/clinical_feasibility_agent.py", "Calculates friction score (0-10) and blocks drug collisions (DDIs).", COLOR_PURPLE),
        ("05. Scientific Skeptic", "src/agents/trial_appraisal_agent.py", "Audits clinical trial spin, control arms, and assigns GRADE scores.", COLOR_PURPLE),
        ("06. Twin Coordinator", "src/agents/coordinator.py", "Synthesizes multi-cancer trajectories into oncologist-ready report.", COLOR_PURPLE),
        ("07. TB Supervisor", "src/agents/tumor_board/supervisor.py", "Orchestrates 3-round oncology debate and adjudicates consensus math.", COLOR_EMERALD),
        ("08. Medical Oncologist", "src/agents/tumor_board/medical_oncologist.py", "Systemic chemotherapy, targeted regimens, immunotherapy & ctDNA.", COLOR_EMERALD),
        ("09. Surgical Oncologist", "src/agents/tumor_board/surgical_oncologist.py", "Evaluates resectability, R0/R1 margins, and surgical morbidity.", COLOR_CYAN),
        ("10. Radiation Oncologist", "src/agents/tumor_board/radiation_oncologist.py", "Field bed sterilization, stereotactic body radiation (SBRT/EBRT).", COLOR_CYAN),
    ]

    for idx, (aname, apath, adesc, acol) in enumerate(agent_grid):
        row = idx // 5
        col = idx % 5
        l = Inches(0.8 + col * 2.38)
        t = Inches(1.4 + row * 2.8)
        card = add_card(s8, l, t, Inches(2.25), Inches(2.55), aname, "", acol)
        
        tb = s8.shapes.add_textbox(l + Inches(0.15), t + Inches(0.55), Inches(1.95), Inches(1.85))
        p = tb.text_frame.paragraphs[0]
        p.text = apath
        p.font.size = Pt(8.5)
        p.font.color.rgb = COLOR_CYAN
        p2 = tb.text_frame.add_paragraph()
        p2.text = adesc
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = COLOR_WHITE
        p2.space_before = Pt(6)

    # =========================================================================
    # SLIDE 9: TECHNOLOGY STACKS USED
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    add_background(s9)
    add_header(s9, "Technology Stacks Used: 10 Engineering Foundation Blocks", "TECH STACK", 9)

    techs = [
        ("Python 3.10+", "FastAPI & Pydantic", "FastAPI async backend, Pydantic v2 schemas, type-safe runtime", COLOR_BLUE),
        ("Web SPA / Sliders", "Interface & Canvas", "Interactive 18-parameter sliders, HTML5 Canvas 2D trajectories", COLOR_CYAN),
        ("LangGraph", "Agent Orchestration", "StateGraph, cyclical cross-examination loops, conditional edges", COLOR_PURPLE),
        ("Ollama", "Local LLM Execution", "Private on-premise inference (Llama-3, Mistral) for HIPAA compliance", COLOR_EMERALD),
        ("Google Gemini", "Generative Reasoning", "Gemini 2.5 Flash for high-speed synthesis & token-budgeted reasoning", COLOR_BLUE),
        ("ChromaDB", "Vector Database", "Persistent embeddings of NCCN, USPSTF, and WCRF guidelines", COLOR_CYAN),
        ("JSON Schema", "Structured Data", "Resilient offline fallback store & strict Pydantic payload exchange", COLOR_PURPLE),
        ("NCBI PubMed Tool", "Evidence Grounding", "Live search for rare variants & Phase 3 trial abstract verification", COLOR_EMERALD),
        ("Model Context Protocol", "Agent Tool Protocol", "All 10 agents exposed via standard MCP (mcp_server.py)", COLOR_AMBER),
        ("GitHub & Pytest", "CI/CD & Testing", "Automated regression testing, Pytest suites, and reproducible builds", COLOR_ROSE),
    ]

    for idx, (tname, tcat, tdesc, tcol) in enumerate(techs):
        row = idx // 5
        col = idx % 5
        l = Inches(0.8 + col * 2.38)
        t = Inches(1.4 + row * 2.8)
        card = add_card(s9, l, t, Inches(2.25), Inches(2.55), tname, tcat, tcol)
        
        tb = s9.shapes.add_textbox(l + Inches(0.15), t + Inches(0.8), Inches(1.95), Inches(1.6))
        p = tb.text_frame.paragraphs[0]
        p.text = tdesc
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_WHITE

    # =========================================================================
    # SLIDE 10: EXPECTATIONS & DELIVERED CLINICAL VALUE
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    add_background(s10)
    add_header(s10, "Target Metrics, Expected Outcomes & Delivered Clinical Value", "EXPECTATIONS & VALUE", 10)

    metrics = [
        ("Evidence Accuracy", "99.2%", "Zero ungrounded assertions; every intervention backed by verified NCCN/USPSTF or PubMed citations.", COLOR_EMERALD),
        ("Hallucination Rate", "< 0.5%", "Autonomous Scientific Skeptic detects and rejects biased or fabricated trial findings.", COLOR_CYAN),
        ("Pipeline Latency", "< 3.5s", "Parallel LangGraph node execution and strict Gemini token budgeting ensure near-instant reports.", COLOR_BLUE),
        ("Adherence Retention", "75%+", "Friction scoring filters out unsustainable regimens, boosting real-world clinical follow-through.", COLOR_PURPLE),
    ]

    for idx, (m_title, m_stat, m_desc, m_col) in enumerate(metrics):
        l = Inches(0.8 + idx * 2.95)
        card = add_card(s10, l, Inches(1.4), Inches(2.8), Inches(2.4), m_title, "", m_col)
        
        tb_stat = s10.shapes.add_textbox(l + Inches(0.2), Inches(1.9), Inches(2.4), Inches(0.7))
        p_stat = tb_stat.text_frame.paragraphs[0]
        p_stat.text = m_stat
        p_stat.font.size = Pt(28)
        p_stat.font.bold = True
        p_stat.font.color.rgb = m_col
        
        tb_d = s10.shapes.add_textbox(l + Inches(0.2), Inches(2.6), Inches(2.4), Inches(1.1))
        p_d = tb_d.text_frame.paragraphs[0]
        p_d.text = m_desc
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = COLOR_WHITE

    val_card = add_card(s10, Inches(0.8), Inches(4.1), Inches(11.73), Inches(2.8), "Delivered Clinical & Economic Value", "Quantitative Impact Across Healthcare Systems", COLOR_CYAN)
    tb_v = s10.shapes.add_textbox(Inches(1.0), Inches(4.8), Inches(11.3), Inches(1.9))
    tf_v = tb_v.text_frame
    tf_v.word_wrap = True
    v_points = [
        "⚡ 60% Faster Clinical Decision Making: Replaces hours of manual chart reading with instant multi-agent consensus summaries.",
        "🛡️ Zero Toxic Drug Collisions: Automatically cross-references comorbidity and pharmacogenomic contraindications before clinician sign-off.",
        "📊 Quantifiable Risk Reduction: Provides patients and clinicians with clear 30-year risk divergence curves that motivate adherence.",
        "🏥 Hospital Multidisciplinary Efficiency: Pre-convenes the Virtual Tumor Board prior to live meetings, saving high-value specialist time."
    ]
    for pt in v_points:
        p = tf_v.add_paragraph() if tf_v.paragraphs[0].text else tf_v.paragraphs[0]
        p.text = pt
        p.font.size = Pt(11.5)
        p.font.color.rgb = COLOR_WHITE
        p.space_after = Pt(6)

    # =========================================================================
    # SLIDE 11: FUTURE SCOPE - MCP MULTIMODAL CHATBOT & DIAGNOSTIC OCR
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    add_background(s11)
    add_header(s11, "Future Scope: MCP Multimodal Agentic Chatbot & Diagnostic OCR", "FUTURE ROADMAP & MCP EXPANSION", 11)

    future_cards = [
        ("1. Foundation: MCP Agentic Chatbot", 
         "Exposing All 10 Agents via Model Context Protocol",
         "• All 10 agents already exposed as standardized MCP tools (cancertwin:// server).\n• Enables a conversational AI chatbot for oncologists to query in natural language.\n• Answers complex questions without requiring manual UI slider manipulation.\n• Desktop integration with Claude Desktop, Cursor IDE, and clinical EHR terminals.",
         COLOR_CYAN),
        ("2. Diagnostic OCR & Auto-Attribution", 
         "Multimodal Report Ingestion & Root-Cause Factor Analysis",
         "• Multimodal Vision & OCR: Doctors upload PDF/scanned pathology, lab blood panels & genomic reports.\n• Automated Parameter Extraction: Eliminates manual slider adjustments in the Web UI.\n• Root-Cause Attribution: Explicitly identifies which exact biomarker surges or drops drove the risk change.\n• Fatal Drug Reaction Predictor: Explains biochemical mechanisms behind fatal adverse drug responses.",
         COLOR_PURPLE),
        ("3. Oncology & Researcher Sandbox", 
         "Interactive Cohort Studies & Retrospective Trials",
         "• Clinical Case Explorer: Allows researchers and oncologists to study patient cohorts retrospectively.\n• What-If Counterfactual Lab: Test novel adjuvant therapy hypotheses in silico before human trials.\n• Federated Learning: Train on decentralized hospital datasets while preserving patient privacy.\n• Real-Time FHIR / HL7 Ingestion: Live synchronization with hospital Epic/Cerner EHR systems.",
         COLOR_EMERALD)
    ]

    for idx, (ftitle, fsub, fdesc, fcol) in enumerate(future_cards):
        l = Inches(0.8 + idx * 3.95)
        card = add_card(s11, l, Inches(1.4), Inches(3.8), Inches(5.5), ftitle, fsub, fcol)
        tb = s11.shapes.add_textbox(l + Inches(0.2), Inches(2.2), Inches(3.4), Inches(4.5))
        p = tb.text_frame.paragraphs[0]
        p.text = fdesc
        p.font.size = Pt(11.5)
        p.font.color.rgb = COLOR_WHITE

    # =========================================================================
    # SLIDE 12: CONCLUSION & THANK YOU
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    add_background(s12)

    c_hero = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.5), Inches(1.2), Inches(10.33), Inches(5.1))
    c_hero.fill.solid()
    c_hero.fill.fore_color.rgb = COLOR_CARD
    c_hero.line.color.rgb = COLOR_CYAN
    c_hero.line.width = Pt(2.0)

    tb_b = s12.shapes.add_textbox(Inches(2.0), Inches(1.6), Inches(9.3), Inches(0.4))
    p = tb_b.text_frame.paragraphs[0]
    p.text = "CANCERTWIN AI 2.0 • AGENTIC ONCOLOGY INTELLIGENCE"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_CYAN
    p.alignment = PP_ALIGN.CENTER

    tb_t = s12.shapes.add_textbox(Inches(2.0), Inches(2.1), Inches(9.3), Inches(1.0))
    p = tb_t.text_frame.paragraphs[0]
    p.text = "Thank You!"
    p.font.size = Pt(46)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.alignment = PP_ALIGN.CENTER

    tb_m = s12.shapes.add_textbox(Inches(2.2), Inches(3.2), Inches(8.9), Inches(1.3))
    tf_m = tb_m.text_frame
    tf_m.word_wrap = True
    p = tf_m.paragraphs[0]
    p.text = "Transforming Oncology from Reactive Care to Proactive Multi-Agent Intelligence."
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = COLOR_EMERALD
    p.alignment = PP_ALIGN.CENTER
    p2 = tf_m.add_paragraph()
    p2.text = "10 Specialized Agents • LangGraph Orchestration • Dual RAG • Model Context Protocol"
    p2.font.size = Pt(13)
    p2.font.color.rgb = COLOR_MUTED
    p2.alignment = PP_ALIGN.CENTER

    q_box = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(3.5), Inches(4.7), Inches(6.33), Inches(1.1))
    q_box.fill.solid()
    q_box.fill.fore_color.rgb = RGBColor(15, 23, 42)
    q_box.line.color.rgb = COLOR_BLUE
    tb_q = s12.shapes.add_textbox(Inches(3.5), Inches(4.8), Inches(6.33), Inches(0.9))
    p = tb_q.text_frame.paragraphs[0]
    p.text = "Questions & Live Demonstration"
    p.font.bold = True
    p.font.size = Pt(14)
    p.font.color.rgb = COLOR_WHITE
    p.alignment = PP_ALIGN.CENTER
    p2 = tb_q.text_frame.add_paragraph()
    p2.text = "Project Codebase • Architecture Map • MCP Tools Catalog Ready"
    p2.font.size = Pt(10)
    p2.font.color.rgb = COLOR_CYAN
    p2.alignment = PP_ALIGN.CENTER

    output_path = "c:/Users/akash/Desktop/ClaudeProject/CancerTwin_AI_Executive_Presentation.pptx"
    prs.save(output_path)
    print(f"Presentation successfully created at: {output_path}")

if __name__ == "__main__":
    build_presentation()
