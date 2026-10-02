"""
CancerTwin AI 2.0 - Model Context Protocol (MCP) Server.
Standard JSON-RPC 2.0 stdio server compliant with Claude Desktop, Cursor, and MCP clients.

Exposes:
1. Tools:
   - search_pubmed_literature (Live PubMed E-Utilities query)
   - lookup_genomic_variant (Oncogenic mutation actionability & targeted therapies)
   - query_cancertwin_knowledge (ChromaDB 100-guideline RAG with metadata filtering)
   - convene_tumor_board (3-Specialist multidisciplinary debate & consensus)
   - simulate_patient_interventions (Digital Twin What-If counterfactual modeling)
2. Resources:
   - cancertwin://guidelines/catalog (Full catalogue of 100 clinical guidelines)
"""

import sys
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

# Setup logging to stderr (stdio stdout is reserved for JSON-RPC messages)
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CancerTwin-MCP")

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.tools.pubmed_tool import PubMedTool
from src.rag.retriever import OncologyRetriever
from src.models.oncology_history import PriorCancerHistory, ProceduresPerformed, TumorBiomarkers
from src.agents.tumor_board.supervisor import TumorBoardSupervisorAgent
from src.models.patient import PatientProfile, LifestyleFactors, EnvironmentalFactors, ScreeningHistory, GeneticHistory
from src.models.simulation import WhatIfScenario, InterventionParameters
from src.agents.coordinator import TwinCoordinatorAgent

pubmed_tool = PubMedTool()
retriever = OncologyRetriever()
tb_supervisor = TumorBoardSupervisorAgent()
coordinator = TwinCoordinatorAgent(retriever=retriever)

# Tool Schemas for MCP
TOOLS = [
    {
        "name": "search_pubmed_literature",
        "description": "Searches NCBI PubMed live clinical literature. Use this when local guidelines lack information on rare cancer mutations, novel targeted therapies, or newly published trials.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Medical search query (e.g. 'NTRK gene fusion targeted therapy sarcoma', 'HER2 exon 20 insertion lung cancer')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of literature records to retrieve (default: 3)",
                    "default": 3
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "lookup_genomic_variant",
        "description": "Queries clinical actionability, FDA-approved targeted therapies, and trials for specific oncogenic mutations (e.g. BRAF V600E, KRAS G12C, RET fusion, NTRK fusion).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "gene": {
                    "type": "string",
                    "description": "Gene symbol (e.g. 'BRAF', 'KRAS', 'EGFR', 'RET', 'NTRK1')"
                },
                "mutation": {
                    "type": "string",
                    "description": "Specific alteration or protein change (e.g. 'V600E', 'G12C', 'fusion', 'exon 20 insertion')"
                }
            },
            "required": ["gene"]
        }
    },
    {
        "name": "query_cancertwin_knowledge",
        "description": "Queries CancerTwin's curated 100-guideline knowledge base (USPSTF, NCCN, NEJM, Lancet, JAMA) for clinical recommendations, hazard ratios, and relative risk reductions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Clinical search query (e.g. 'LDCT lung screening pack-years', 'ctDNA colorectal recurrence')"
                },
                "cancer_type": {
                    "type": "string",
                    "description": "Optional cancer domain filter ('Lung', 'Colorectal', 'Breast', 'Prostate', 'Cervical', 'Pancreatic', 'Melanoma', 'Liquid Biopsy / ctDNA')",
                    "enum": ["Lung", "Colorectal", "Breast", "Prostate", "Cervical", "Pancreatic", "Melanoma", "Liquid Biopsy / ctDNA", "Environmental", "Lifestyle / Nutrition"]
                },
                "top_k": {
                    "type": "integer",
                    "default": 3
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "convene_tumor_board",
        "description": "Convenes a 3-Specialist Multidisciplinary Virtual Tumor Board (Medical, Surgical, Radiation Oncologist) to debate 5-year relapse hazard and produce an adjudicated consensus action plan.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "primary_cancer": {
                    "type": "string",
                    "description": "Primary cancer histology (e.g. 'Colorectal', 'Lung', 'Breast', 'Prostate')"
                },
                "stage": {
                    "type": "string",
                    "enum": ["Stage I", "Stage II", "Stage III", "Stage IV"],
                    "description": "Stage at diagnosis"
                },
                "surgical_margin": {
                    "type": "string",
                    "enum": ["R0", "R1", "R2"],
                    "description": "Surgical resection margin clearance status (R0=clear, R1=microscopic positive, R2=gross residual)"
                },
                "ctdna_status": {
                    "type": "string",
                    "enum": ["positive", "negative", "unknown"],
                    "description": "Circulating tumor DNA minimal residual disease status"
                },
                "chemotherapy_given": {
                    "type": "boolean",
                    "description": "Whether systemic adjuvant chemotherapy was administered"
                },
                "radiation_given": {
                    "type": "boolean",
                    "description": "Whether adjuvant radiation therapy was delivered"
                },
                "years_in_remission": {
                    "type": "number",
                    "description": "Years patient has been in continuous remission",
                    "default": 2.0
                },
                "psa_ng_ml": {
                    "type": "number",
                    "description": "Serum PSA level if applicable"
                },
                "cea_ng_ml": {
                    "type": "number",
                    "description": "Serum CEA level if applicable"
                }
            },
            "required": ["primary_cancer", "stage", "surgical_margin", "ctdna_status"]
        }
    },
    {
        "name": "simulate_patient_interventions",
        "description": "Executes counterfactual digital twin simulation evaluating baseline vs post-intervention cancer risk reductions across 5 axes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "age": {"type": "integer", "default": 55},
                "biological_sex": {"type": "string", "enum": ["male", "female"]},
                "smoking_status": {"type": "string", "enum": ["never", "former", "current"]},
                "pack_years": {"type": "number", "default": 20.0},
                "bmi": {"type": "number", "default": 27.5},
                "interventions": {
                    "type": "object",
                    "description": "Parameters to optimize (e.g. smoking_cessation: true, target_bmi: 24.0, adhere_screening: true)"
                }
            },
            "required": ["age", "biological_sex"]
        }
    }
]

def handle_tool_call(name: str, arguments: Dict[str, Any]) -> Any:
    """Executes corresponding Python agent or tool logic."""
    if name == "search_pubmed_literature":
        query = arguments.get("query", "")
        max_r = arguments.get("max_results", 3)
        articles = pubmed_tool.search_pubmed(query=query, max_results=max_r)
        return {
            "query": query,
            "total_found": len(articles),
            "articles": articles
        }

    elif name == "lookup_genomic_variant":
        gene = arguments.get("gene", "")
        mutation = arguments.get("mutation")
        result = pubmed_tool.lookup_variant_knowledge(gene=gene, mutation=mutation)
        return result

    elif name == "query_cancertwin_knowledge":
        query = arguments.get("query", "")
        c_type = arguments.get("cancer_type")
        top_k = arguments.get("top_k", 3)
        hits = retriever.retrieve_guidelines(query=query, cancer_type=c_type, top_k=top_k)
        return {
            "query": query,
            "cancer_type_filter": c_type,
            "evidence_count": len(hits),
            "citations": [
                {
                    "title": h.title,
                    "source": h.source,
                    "cancer_type": h.cancer_type,
                    "hazard_ratio": h.hazard_ratio,
                    "evidence_level": h.evidence_level,
                    "url": h.url,
                    "excerpt": h.excerpt
                }
                for h in hits
            ]
        }

    elif name == "convene_tumor_board":
        history = PriorCancerHistory(
            has_prior_cancer=True,
            primary_cancer_type=arguments.get("primary_cancer", "Colorectal"),
            stage_at_diagnosis=arguments.get("stage", "Stage III"),
            years_in_remission=arguments.get("years_in_remission", 2.0),
            procedures=ProceduresPerformed(
                surgery_performed=True,
                surgical_margin=arguments.get("surgical_margin", "R0"),
                chemotherapy=arguments.get("chemotherapy_given", False),
                radiation_therapy=arguments.get("radiation_given", False)
            ),
            biomarkers=TumorBiomarkers(
                ctdna_status=arguments.get("ctdna_status", "negative"),
                psa_ng_ml=arguments.get("psa_ng_ml"),
                cea_ng_ml=arguments.get("cea_ng_ml")
            )
        )
        debate = tb_supervisor.adjudicate_debate(history)
        return {
            "primary_cancer": debate.primary_cancer,
            "stage": debate.stage,
            "consensus_5yr_relapse_risk_pct": debate.consensus_relapse_risk_5yr_pct,
            "risk_tier": debate.risk_tier,
            "adjudication_summary": debate.adjudication_rationale,
            "specialist_opinions": [
                {
                    "specialist": op.specialist_name,
                    "role": op.agent_role,
                    "assessed_risk_pct": op.assessed_relapse_risk_pct,
                    "concerns": op.key_concerns,
                    "interventions": op.recommended_interventions
                }
                for op in debate.agent_opinions
            ],
            "action_plan": debate.action_plan,
            "cited_trials": [
                {"title": c.title, "source": c.source, "url": c.url, "hr": c.hazard_ratio}
                for c in debate.evidence_citations
            ]
        }

    elif name == "simulate_patient_interventions":
        profile = PatientProfile(
            patient_id="PT-MCP-CLIENT",
            age=arguments.get("age", 55),
            biological_sex=arguments.get("biological_sex", "female"),
            lifestyle=LifestyleFactors(
                smoking_status=arguments.get("smoking_status", "former"),
                pack_years=arguments.get("pack_years", 20.0),
                bmi=arguments.get("bmi", 27.0)
            ),
            environmental=EnvironmentalFactors(),
            screening=ScreeningHistory(),
            genetics=GeneticHistory()
        )
        report = coordinator.run(profile)
        return {
            "patient_id": report.twin_id,
            "health_score": report.patient_summary.get("health_score"),
            "baseline_risk_aggregate": report.aggregate_baseline_risk_score,
            "simulated_risk_aggregate": report.aggregate_simulated_risk_score,
            "preventive_opportunities": report.primary_preventive_opportunities,
            "executive_narrative": report.clinical_narrative
        }

    else:
        raise ValueError(f"Unknown tool name: {name}")

def send_response(response: Dict[str, Any]):
    """Encodes and writes a JSON-RPC message to stdout."""
    payload = json.dumps(response)
    sys.stdout.write(payload + "\n")
    sys.stdout.flush()

def run_mcp_server():
    """Main stdio loop listening for JSON-RPC 2.0 requests from MCP hosts."""
    logger.info("CancerTwin AI MCP Server initialized on stdio. Awaiting client handshake...")

    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
        except Exception as e:
            logger.error(f"Malformed JSON: {e}")
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        # Handle Protocol Methods
        if method == "initialize":
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {}
                    },
                    "serverInfo": {
                        "name": "cancertwin-mcp-server",
                        "version": "2.0.0"
                    }
                }
            })

        elif method == "notifications/initialized":
            logger.info("Client completed initialization handshake.")

        elif method == "tools/list":
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": TOOLS
                }
            })

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            logger.info(f"Tool invocation: {tool_name}")
            try:
                result_data = handle_tool_call(tool_name, tool_args)
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result_data, indent=2)
                            }
                        ]
                    }
                })
            except Exception as e:
                logger.error(f"Error in tool {tool_name}: {e}")
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "isError": True,
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                })

        elif method == "resources/list":
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "resources": [
                        {
                            "uri": "cancertwin://guidelines/catalog",
                            "name": "CancerTwin 100 Oncology Guidelines Catalog",
                            "mimeType": "application/json",
                            "description": "Full inventory of 100 clinical trials and guidelines with verified PubMed/NEJM/Lancet URLs"
                        }
                    ]
                }
            })

        elif method == "resources/read":
            uri = params.get("uri")
            if uri == "cancertwin://guidelines/catalog":
                from src.rag.vector_store import ChromaManager
                cm = ChromaManager()
                docs = cm.get_all_documents() if hasattr(cm, "get_all_documents") else cm._fallback_docs
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "contents": [
                            {
                                "uri": uri,
                                "mimeType": "application/json",
                                "text": json.dumps(docs, indent=2)
                            }
                        ]
                    }
                })
            else:
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32602, "message": f"Resource not found: {uri}"}
                })

        elif method == "ping":
            send_response({"jsonrpc": "2.0", "id": req_id, "result": {}})

        else:
            if req_id is not None:
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method '{method}' not implemented."}
                })

if __name__ == "__main__":
    run_mcp_server()
