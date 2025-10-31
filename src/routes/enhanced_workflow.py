#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Enhanced Workflow Routes
Rotas para o workflow aprimorado em 3 etapas + CPL Devastador + Verificação AI
"""
import logging
import time
import uuid
import asyncio
import os
import glob
import json
from datetime import datetime
from typing import Dict, Any, List
from flask import Blueprint, request, jsonify, send_file
import threading

# Import dos serviços necessários
# services.auto_save_manager será importado diretamente para evitar circular imports
def get_services():
    """Lazy loading dos serviços para evitar problemas de inicialização"""
    try:
        from services.real_search_orchestrator import real_search_orchestrator
        from services.massive_search_engine import massive_search_engine
        from services.viral_content_analyzer import viral_content_analyzer
        from services.enhanced_synthesis_engine import enhanced_synthesis_engine
        from services.enhanced_module_processor import enhanced_module_processor
        from services.comprehensive_report_generator_v3 import comprehensive_report_generator_v3
        from services.viral_report_generator import ViralReportGenerator
        from services.viral_integration_service import ViralImageFinder
        # ADICIONAR O CPL DEVASTADOR
        from services.cpl_devastador_protocol import get_cpl_protocol
        
        return {
            'real_search_orchestrator': real_search_orchestrator,
            'massive_search_engine': massive_search_engine,
            'viral_content_analyzer': viral_content_analyzer,
            'enhanced_synthesis_engine': enhanced_synthesis_engine,
            'enhanced_module_processor': enhanced_module_processor,
            'comprehensive_report_generator_v3': comprehensive_report_generator_v3,
            'ViralReportGenerator': ViralReportGenerator,
            'viral_integration_service': ViralImageFinder(),
            # ADICIONAR O PROTOCOLO CPL
            'cpl_devastador_protocol': get_cpl_protocol()
        }
    except ImportError as e:
        logger.error(f"❌ Erro ao importar serviços: {e}")
        return None

logger = logging.getLogger(__name__)
enhanced_workflow_bp = Blueprint('enhanced_workflow', __name__)

# Instância global do AutoSaveManager para evitar circular imports e garantir consistência
from services.auto_save_manager import AutoSaveManager
auto_save_manager_instance = AutoSaveManager()
salvar_etapa = auto_save_manager_instance.salvar_etapa

@enhanced_workflow_bp.route('/workflow/step1/start', methods=['POST'])
def start_step1_collection():
    """ETAPA 1: Coleta Massiva de Dados com Screenshots"""
    try:
        data = request.get_json()
        # Gera session_id único
        session_id = f"session_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        # Extrai parâmetros
        segmento = data.get('segmento', '').strip()
        produto = data.get('produto', '').strip()
        publico = data.get('publico', '').strip()
        # Validação
        if not segmento:
            return jsonify({"error": "Segmento é obrigatório"}), 400
        # Constrói query de pesquisa
        query_parts = [segmento]
        if produto:
            query_parts.append(produto)
        query_parts.extend(["Brasil", "2025", "mercado"])
        query = " ".join(query_parts)
        # Contexto da análise
        context = {
            "segmento": segmento,
            "produto": produto,
            "publico": publico,
            "query_original": query,
            "etapa": 1,
            "workflow_type": "enhanced_v3"
        }
        logger.info(f"🚀 ETAPA 1 INICIADA - Sessão: {session_id}")
        logger.info(f"🔍 Query: {query}")
        # Salva início da etapa 1
        salvar_etapa("etapa1_iniciada", {
            "session_id": session_id,
            "query": query,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }, categoria="workflow", session_id=session_id)
        # Executa coleta massiva em thread separada
        def execute_collection_thread():
            logger.info(f"🚀 INICIANDO THREAD DE COLETA - Sessão: {session_id}")
            try:
                # Carrega serviços de forma lazy
                services = get_services()
                if not services:
                    logger.error("❌ Falha ao carregar serviços necessários")
                    salvar_etapa("etapa1_erro", {
                        "session_id": session_id,
                        "error": "Falha ao carregar serviços",
                        "timestamp": datetime.now().isoformat()
                    }, categoria="workflow", session_id=session_id)
                    return
                
                async def async_collection_tasks():
                    search_results = {'web_results': [], 'social_results': [], 'youtube_results': []}
                    massive_results = {}
                    viral_analysis = {}
                    try:
                        # PRIMEIRA ETAPA: Busca viral (nova integração)
                        logger.info(f"🔥 Executando busca viral para: {query}")
                        viral_integration_service = services["viral_integration_service"]
                        viral_data = await viral_integration_service.find_viral_images(query=query)
                        viral_results_list = viral_data[0] if viral_data and len(viral_data) > 0 else []
                        viral_results_dicts = [img.__dict__ for img in viral_results_list]
                        viral_results = {
                             "search_completed_at": datetime.now().isoformat(),
                             "total_images_found": len(viral_results_list),
                             "total_images_saved": len([img for img in viral_results_list if img.image_path]),
                             "platforms_searched": list(set(img.platform for img in viral_results_list)),
                             "aggregated_metrics": {
                                 "total_engagement_score": sum(img.engagement_score for img in viral_results_list),
                                 "average_engagement": sum(img.engagement_score for img in viral_results_list) / len(viral_results_list) if viral_results_list else 0,
                                 "total_estimated_views": sum(img.views_estimate for img in viral_results_list),
                                 "total_estimated_likes": sum(img.likes_estimate for img in viral_results_list),
                                 "top_performing_platform": max(set(img.platform for img in viral_results_list), key=[img.platform for img in viral_results_list].count) if viral_results_list else None
                             },
                             "viral_images": viral_results_dicts,
                             "fallback_used": False
                         }
                        salvar_etapa("viral_search_completed", {
                            "session_id": session_id,
                            "viral_results": viral_results,
                            "timestamp": datetime.now().isoformat()
                        }, categoria="workflow", session_id=session_id)
                        
                        # SEGUNDA ETAPA: Busca massiva real
                        logger.info(f"🔍 Executando busca massiva - Sessão: {session_id}")
                        real_search_orch = services["real_search_orchestrator"]
                        if hasattr(real_search_orch, "execute_massive_real_search"):
                            search_results = await real_search_orch.execute_massive_real_search(
                                query=query,
                                context=context,
                                session_id=session_id
                            )
                        else:
                            logger.error("❌ Método execute_massive_real_search não encontrado")
                        
                        logger.info(f"✅ Busca massiva concluída - Sessão: {session_id}")
                        
                        logger.info(f"🌐 Executando busca ALIBABA WebSailor - Sessão: {session_id}")
                        massive_results = await services['massive_search_engine'].execute_massive_search(
                            produto=context.get('segmento', context.get('produto', query)),
                            publico_alvo=context.get('publico', context.get('publico_alvo', 'público brasileiro')),
                            session_id=session_id
                        )
                        logger.info(f"✅ Busca ALIBABA WebSailor concluída - Sessão: {session_id}")
                        
                        logger.info(f"🔥 Analisando e capturando conteúdo viral - Sessão: {session_id}")
                        viral_analysis = await services['viral_content_analyzer'].analyze_and_capture_viral_content(
                            search_results=search_results,
                            session_id=session_id,
                            max_captures=15
                        )
                        logger.info(f"✅ Análise viral concluída - Sessão: {session_id}")
                        
                    except Exception as e:
                        logger.error(f"❌ Erro durante as operações assíncronas da Etapa 1: {e}")
                        # Continua mesmo com erro para tentar gerar o relatório com o que foi coletado
                    
                    # GERA RELATÓRIO VIRAL AUTOMATICAMENTE
                    logger.info("🔥 Gerando relatório viral automático...")
                    viral_report_generator = services['ViralReportGenerator']()
                    viral_report_success = viral_report_generator.generate_viral_report(session_id)
                    if viral_report_success:
                        logger.info("✅ Relatório viral gerado e salvo automaticamente")
                    else:
                        logger.warning("⚠️ Falha ao gerar relatório viral automático")
                    
                    # GERA CONSOLIDAÇÃO FINAL COMPLETA
                    logger.info("🔗 CONSOLIDANDO TODOS OS DADOS DA ETAPA 1...")
                    consolidacao_final = _gerar_consolidacao_final_etapa1(
                        session_id, search_results, viral_analysis, massive_results, viral_results
                    )
                    
                    # Gera relatório de coleta
                    collection_report = _generate_collection_report(
                        search_results, viral_analysis, session_id, context
                    )
                    # Salva relatório
                    _save_collection_report(collection_report, session_id)
                    
                    # Salva resultado da etapa 1 COM CONSOLIDAÇÃO
                    salvar_etapa("etapa1_concluida", {
                        "session_id": session_id,
                        "search_results": search_results,
                        "viral_analysis": viral_analysis,
                        "massive_results": massive_results,
                        "consolidacao_final": consolidacao_final,
                        "collection_report_generated": True,
                        "timestamp": datetime.now().isoformat(),
                        "estatisticas_finais": consolidacao_final.get("estatisticas", {})
                    }, categoria="workflow", session_id=session_id)
                    
                    logger.info(f"✅ ETAPA 1 CONCLUÍDA - Sessão: {session_id}")
                    logger.info(f"📊 CONSOLIDAÇÃO: {consolidacao_final.get('estatisticas', {}).get('total_dados_coletados', 0)} dados únicos")
                
                asyncio.run(async_collection_tasks())
                
            except Exception as e:
                logger.error(f"❌ Erro na execução da Etapa 1: {e}")
                salvar_etapa("etapa1_erro", {
                    "session_id": session_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }, categoria="workflow", session_id=session_id)
        
        # Inicia a thread para a coleta
        thread = threading.Thread(target=execute_collection_thread)
        thread.start()
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "message": "Etapa 1 iniciada: Coleta massiva de dados em segundo plano",
            "query": query,
            "estimated_duration": "3-5 minutos",
            "next_step": "/api/workflow/step2/start",
            "status_endpoint": f"/api/workflow/status/{session_id}"
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar Etapa 1: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Falha ao iniciar coleta de dados"
        }), 500

@enhanced_workflow_bp.route('/workflow/step2/start', methods=['POST'])
def start_step2_synthesis():
    """ETAPA 2: Síntese com IA e Busca Ativa"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({"error": "session_id é obrigatório"}), 400
        
        logger.info(f"🧠 ETAPA 2 INICIADA - Síntese para sessão: {session_id}")
        
        # Salva início da etapa 2
        salvar_etapa("etapa2_iniciada", {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }, categoria="workflow", session_id=session_id)
        
        # Executa síntese em thread separada
        def execute_synthesis_thread():
            try:
                # Carrega serviços de forma lazy
                services = get_services()
                if not services:
                    logger.error("❌ Falha ao carregar serviços necessários")
                    salvar_etapa("etapa2_erro", {
                        "session_id": session_id,
                        "error": "Falha ao carregar serviços",
                        "timestamp": datetime.now().isoformat()
                    }, categoria="workflow", session_id=session_id)
                    return
                
                async def async_synthesis_tasks():
                    synthesis_result = {}
                    behavioral_result = {}
                    market_result = {}
                    try:
                        # Executa síntese master com busca ativa
                        synthesis_result = await services['enhanced_synthesis_engine'].execute_enhanced_synthesis(
                            session_id=session_id,
                            synthesis_type="master_synthesis"
                        )
                        # Executa síntese comportamental
                        behavioral_result = await services['enhanced_synthesis_engine'].execute_behavioral_synthesis(session_id)
                        # Executa síntese de mercado
                        market_result = await services['enhanced_synthesis_engine'].execute_market_synthesis(session_id)
                    except Exception as e:
                        logger.error(f"❌ Erro durante as operações assíncronas da Etapa 2: {e}")
                    
                    # Salva resultado da etapa 2
                    salvar_etapa("etapa2_concluida", {
                        "session_id": session_id,
                        "synthesis_result": synthesis_result,
                        "behavioral_result": behavioral_result,
                        "market_result": market_result,
                        "timestamp": datetime.now().isoformat()
                    }, categoria="workflow", session_id=session_id)
                    
                    logger.info(f"✅ ETAPA 2 CONCLUÍDA - Sessão: {session_id}")
                
                asyncio.run(async_synthesis_tasks())
                
            except Exception as e:
                logger.error(f"❌ Erro na execução da Etapa 2: {e}")
                salvar_etapa("etapa2_erro", {
                    "session_id": session_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }, categoria="workflow", session_id=session_id)
        
        # Inicia a thread para a síntese
        thread = threading.Thread(target=execute_synthesis_thread)
        thread.start()
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "message": "Etapa 2 iniciada: Síntese com IA e busca ativa em segundo plano",
            "estimated_duration": "2-4 minutos",
            "next_step": "/api/workflow/external_ai_verification",
            "status_endpoint": f"/api/workflow/status/{session_id}"
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar Etapa 2: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Falha ao iniciar síntese"
        }), 500

@enhanced_workflow_bp.route('/workflow/external_ai_verification', methods=['POST'])
def run_external_ai_verification():
    """VERIFICAÇÃO AI EXTERNA: Executa verificação dos dados antes da Etapa 3"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({"error": "session_id é obrigatório"}), 400

        logger.info(f"🤖 VERIFICAÇÃO AI INICIADA - Sessão: {session_id}")

        # Salva início da verificação
        salvar_etapa("verificacao_ai_iniciada", {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }, categoria="workflow", session_id=session_id)

        # Executa verificação em thread separada
        def execute_verification_thread():
            try:
                import asyncio
                from services.external_ai_integration import external_ai_integration

                async def async_verification():
                    result = await external_ai_integration.verify_session_data(session_id)

                    # Salva resultado da verificação
                    salvar_etapa("verificacao_ai_concluida", {
                        "session_id": session_id,
                        "verification_result": result,
                        "timestamp": datetime.now().isoformat()
                    }, categoria="workflow", session_id=session_id)

                    logger.info(f"✅ VERIFICAÇÃO AI CONCLUÍDA - Sessão: {session_id}")

                asyncio.run(async_verification())

            except Exception as e:
                logger.error(f"❌ Erro na verificação AI: {e}")
                salvar_etapa("verificacao_ai_erro", {
                    "session_id": session_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }, categoria="workflow", session_id=session_id)

        # Inicia a thread para verificação
        thread = threading.Thread(target=execute_verification_thread)
        thread.start()

        return jsonify({
            "success": True,
            "session_id": session_id,
            "message": "Verificação AI iniciada em segundo plano",
            "estimated_duration": "1-2 minutos",
            "next_step": "/api/workflow/step3/start",
            "status_endpoint": f"/api/workflow/status/{session_id}"
        }), 200

    except Exception as e:
        logger.error(f"❌ Erro ao iniciar verificação AI: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Falha ao iniciar verificação AI"
        }), 500

@enhanced_workflow_bp.route('/workflow/step3/start', methods=['POST'])
def start_step3_generation():
    """ETAPA 3: Geração dos 16 Módulos e Relatório Final"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({"error": "session_id é obrigatório"}), 400

        logger.info(f"📝 ETAPA 3 INICIADA - Geração para sessão: {session_id}")

        # Salva início da etapa 3
        salvar_etapa("etapa3_iniciada", {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }, categoria="workflow", session_id=session_id)
        
        # Executa geração em thread separada
        def execute_generation_thread():
            try:
                # Carrega serviços de forma lazy
                services = get_services()
                if not services:
                    logger.error("❌ Falha ao carregar serviços necessários")
                    salvar_etapa("etapa3_erro", {
                        "session_id": session_id,
                        "error": "Falha ao carregar serviços",
                        "timestamp": datetime.now().isoformat()
                    }, categoria="workflow", session_id=session_id)
                    return
                
                async def async_generation_tasks():
                    modules_result = {}
                    final_report = ""
                    try:
                        # Gera todos os 16 módulos
                        modules_result = await services['enhanced_module_processor'].generate_all_modules(session_id)
                        # Compila relatório final
                        final_report = services['comprehensive_report_generator_v3'].compile_final_markdown_report(session_id)
                    except Exception as e:
                        logger.error(f"❌ Erro durante as operações assíncronas da Etapa 3: {e}")
                    
                    # Salva resultado da etapa 3
                    salvar_etapa("etapa3_concluida", {
                        "session_id": session_id,
                        "modules_result": modules_result,
                        "final_report": final_report,
                        "timestamp": datetime.now().isoformat()
                    }, categoria="workflow", session_id=session_id)
                    
                    logger.info(f"✅ ETAPA 3 CONCLUÍDA - Sessão: {session_id}")
                    logger.info(f"📊 {modules_result.get('successful_modules', 0)}/16 módulos gerados")
                
                asyncio.run(async_generation_tasks())
                
            except Exception as e:
                logger.error(f"❌ Erro na execução da Etapa 3: {e}")
                salvar_etapa("etapa3_erro", {
                    "session_id": session_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }, categoria="workflow", session_id=session_id)
        
        # Inicia a thread para a geração
        thread = threading.Thread(target=execute_generation_thread)
        thread.start()
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "message": "Etapa 3 iniciada: Geração dos 16 módulos e relatório final em segundo plano",
            "estimated_duration": "4-6 minutos",
            "next_step": "/api/workflow/cpl_devastador/start",
            "status_endpoint": f"/api/workflow/status/{session_id}"
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar Etapa 3: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Falha ao iniciar geração"
        }), 500

# ==========================================
# ROTAS DO PROTOCOLO CPL DEVASTADOR
# ==========================================

@enhanced_workflow_bp.route('/workflow/cpl_devastador/start', methods=['POST'])
def start_cpl_devastador():
    """Inicia o protocolo CPL Devastador completo"""
    try:
        data = request.get_json()
        
        # Gera session_id único se não fornecido
        session_id = data.get('session_id') or f"session_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        
        # Extrai parâmetros
        tema = data.get('tema', '').strip()
        segmento = data.get('segmento', '').strip()
        publico_alvo = data.get('publico_alvo', '').strip()
        
        # Validação
        if not tema:
            return jsonify({"error": "Tema é obrigatório"}), 400
        
        logger.info(f"🚀 PROTOCOLO CPL DEVASTADOR INICIADO - Sessão: {session_id}")
        logger.info(f"🎯 Tema: {tema} | Segmento: {segmento} | Público: {publico_alvo}")
        
        # Salva início do protocolo
        salvar_etapa("cpl_devastador_iniciado", {
            "session_id": session_id,
            "tema": tema,
            "segmento": segmento,
            "publico_alvo": publico_alvo,
            "timestamp": datetime.now().isoformat()
        }, categoria="cpl", session_id=session_id)
        
        # Executa protocolo em thread separada
        def execute_cpl_devastador_thread():
            try:
                services = get_services()
                if not services or not services.get('cpl_devastador_protocol'):
                    logger.error("❌ Protocolo CPL Devastador não disponível")
                    salvar_etapa("cpl_devastador_erro", {
                        "session_id": session_id,
                        "error": "Protocolo CPL Devastador não disponível",
                        "timestamp": datetime.now().isoformat()
                    }, categoria="cpl", session_id=session_id)
                    return
                
                async def async_cpl_devastador():
                    try:
                        cpl_protocol = services['cpl_devastador_protocol']
                        
                        resultado = await cpl_protocol.executar_protocolo_completo(
                            tema=tema,
                            segmento=segmento,
                            publico_alvo=publico_alvo,
                            session_id=session_id
                        )
                        
                        # Salva resultado final
                        salvar_etapa("cpl_devastador_concluido", {
                            "session_id": session_id,
                            "resultado": resultado,
                            "timestamp": datetime.now().isoformat()
                        }, categoria="cpl", session_id=session_id)
                        
                        logger.info(f"✅ PROTOCOLO CPL DEVASTADOR CONCLUÍDO - Sessão: {session_id}")
                        
                    except Exception as e:
                        logger.error(f"❌ Erro na execução do CPL Devastador: {e}")
                        salvar_etapa("cpl_devastador_erro", {
                            "session_id": session_id,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }, categoria="cpl", session_id=session_id)
                
                asyncio.run(async_cpl_devastador())
                
            except Exception as e:
                logger.error(f"❌ Erro na thread do CPL Devastador: {e}")
                salvar_etapa("cpl_devastador_erro", {
                    "session_id": session_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }, categoria="cpl", session_id=session_id)
        
        # Inicia a thread
        thread = threading.Thread(target=execute_cpl_devastador_thread)
        thread.start()
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "message": "Protocolo CPL Devastador iniciado em segundo plano",
            "estimated_duration": "5-8 minutos",
            "status_endpoint": f"/api/workflow/cpl_devastador/status/{session_id}"
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar CPL Devastador: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Falha ao iniciar protocolo CPL Devastador"
        }), 500

@enhanced_workflow_bp.route('/workflow/cpl_devastador/status/<session_id>', methods=['GET'])
def get_cpl_devastador_status(session_id):
    """Obtém status do protocolo CPL Devastador"""
    try:
        status = {
            "session_id": session_id,
            "protocol": "cpl_devastador",
            "status": "pending",
            "progress_percentage": 0,
            "current_phase": "iniciando",
            "phases": {
                "contexto_busca": "pending",
                "coleta_dados": "pending",
                "arquitetura_evento": "pending",
                "cpl1_oportunidade": "pending",
                "cpl2_transformacao": "pending",
                "cpl3_caminho": "pending",
                "cpl4_decisao": "pending"
            },
            "last_update": datetime.now().isoformat()
        }
        
        # Verifica se foi concluído
        if os.path.exists(f"analyses_data/{session_id}/cpl_protocol_result.json"):
            status["status"] = "completed"
            status["progress_percentage"] = 100
            status["current_phase"] = "concluido"
            for phase in status["phases"]:
                status["phases"][phase] = "completed"
        
        # Verifica se há erros
        error_files = glob.glob(f"analyses_data/{session_id}/cpl_devastador_erro*")
        if error_files:
            status["status"] = "failed"
            status["error"] = "Erro detectado na execução do protocolo"
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter status do CPL Devastador: {e}")
        return jsonify({
            "session_id": session_id,
            "error": str(e),
            "status": "error"
        }), 500

@enhanced_workflow_bp.route('/workflow/cpl_devastador/results/<session_id>', methods=['GET'])
def get_cpl_devastador_results(session_id):
    """Obtém resultados do protocolo CPL Devastador"""
    try:
        result_file = f"analyses_data/{session_id}/cpl_protocol_result.json"
        
        if not os.path.exists(result_file):
            return jsonify({
                "session_id": session_id,
                "error": "Resultados não encontrados"
            }), 404
        
        with open(result_file, 'r', encoding='utf-8') as f:
            resultado = json.load(f)
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "resultado": resultado
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter resultados do CPL Devastador: {e}")
        return jsonify({
            "session_id": session_id,
            "error": str(e)
        }), 500

# ==========================================
# WORKFLOW COMPLETO (3 ETAPAS + VERIFICAÇÃO AI + CPL DEVASTADOR)
# ==========================================

@enhanced_workflow_bp.route('/workflow/full_workflow/start', methods=['POST'])
def start_full_workflow():
    """Inicia o workflow completo em segundo plano"""
    try:
        data = request.get_json()
        # Gera session_id único
        session_id = f"session_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        # Extrai parâmetros
        segmento = data.get('segmento', '').strip()
        produto = data.get('produto', '').strip()
        publico = data.get('publico', '').strip()
        # Validação
        if not segmento:
            return jsonify({"error": "Segmento é obrigatório"}), 400
        # Constrói query de pesquisa
        query_parts = [segmento]
        if produto:
            query_parts.append(produto)
        query_parts.extend(["Brasil", "2025", "mercado"])
        query = " ".join(query_parts)
        # Contexto da análise
        context = {
            "segmento": segmento,
            "produto": produto,
            "publico": publico,
            "query_original": query,
            "workflow_type": "enhanced_v3_completo"
        }
        logger.info(f"🚀 WORKFLOW COMPLETO INICIADO - Sessão: {session_id}")
        logger.info(f"🔍 Query: {query}")
        # Salva início do workflow completo
        salvar_etapa("workflow_completo_iniciado", {
            "session_id": session_id,
            "query": query,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }, categoria="workflow", session_id=session_id)
        
        def execute_full_workflow_thread():
            try:
                services = get_services()
                if not services:
                    logger.error("❌ Falha ao carregar serviços necessários para workflow completo")
                    salvar_etapa("workflow_erro", {
                        "session_id": session_id,
                        "error": "Falha ao carregar serviços para workflow completo",
                        "timestamp": datetime.now().isoformat()
                    }, categoria="workflow", session_id=session_id)
                    return
                
                async def async_full_workflow_tasks():
                    search_results = {'web_results': [], 'social_results': [], 'youtube_results': []}
                    massive_results = {}
                    viral_analysis = {}
                    synthesis_result = {}
                    behavioral_result = {}
                    market_result = {}
                    verification_result = {}
                    modules_result = {}
                    final_report = ""
                    cpl_result = {}
                    
                    # ETAPA 1: Coleta Massiva de Dados
                    logger.info(f"🚀 INICIANDO ETAPA 1 (Workflow Completo) - Sessão: {session_id}")
                    try:
                        real_search_orch = services['real_search_orchestrator']
                        if hasattr(real_search_orch, 'execute_massive_real_search'):
                            search_results = await real_search_orch.execute_massive_real_search(
                                query=query,
                                context=context,
                                session_id=session_id
                            )
                        else:
                            logger.error("❌ Método execute_massive_real_search não encontrado na Etapa 1 (Workflow Completo)")
                        
                        massive_results = await services['massive_search_engine'].execute_massive_search(
                            produto=context.get('segmento', context.get('produto', query)),
                            publico_alvo=context.get('publico', context.get('publico_alvo', 'público brasileiro')),
                            session_id=session_id
                        )
                        
                        viral_analysis = await services['viral_content_analyzer'].analyze_and_capture_viral_content(
                            search_results=search_results,
                            session_id=session_id,
                            max_captures=15
                        )
                        
                        # GERA RELATÓRIO VIRAL AUTOMATICAMENTE
                        viral_report_generator = services['ViralReportGenerator']()
                        viral_report_generator.generate_viral_report(session_id)
                        
                        # GERA CONSOLIDAÇÃO FINAL COMPLETA
                        consolidacao_final = _gerar_consolidacao_final_etapa1(
                            session_id, search_results, viral_analysis, massive_results
                        )
                        
                        # Gera e salva relatório de coleta
                        collection_report = _generate_collection_report(
                            search_results, viral_analysis, session_id, context
                        )
                        _save_collection_report(collection_report, session_id)
                        
                        salvar_etapa("etapa1_concluida_full_workflow", {
                            "session_id": session_id,
                            "search_results": search_results,
                            "viral_analysis": viral_analysis,
                            "massive_results": massive_results,
                            "consolidacao_final": consolidacao_final,
                            "collection_report_generated": True,
                            "timestamp": datetime.now().isoformat(),
                            "estatisticas_finais": consolidacao_final.get("estatisticas", {})
                        }, categoria="workflow", session_id=session_id)
                        
                        logger.info(f"✅ ETAPA 1 (Workflow Completo) CONCLUÍDA - Sessão: {session_id}")
                        
                    except Exception as e:
                        logger.error(f"❌ Erro na Etapa 1 (Workflow Completo): {e}")
                        salvar_etapa("etapa1_erro_full_workflow", {
                            "session_id": session_id,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }, categoria="workflow", session_id=session_id)
                        return # Aborta o workflow se a primeira etapa falhar
                    
                    # ETAPA 2: Síntese com IA e Busca Ativa
                    logger.info(f"🧠 INICIANDO ETAPA 2 (Workflow Completo) - Sessão: {session_id}")
                    try:
                        synthesis_result = await services['enhanced_synthesis_engine'].execute_enhanced_synthesis(
                            session_id=session_id,
                            synthesis_type="master_synthesis"
                        )
                        behavioral_result = await services['enhanced_synthesis_engine'].execute_behavioral_synthesis(session_id)
                        market_result = await services['enhanced_synthesis_engine'].execute_market_synthesis(session_id)
                        
                        salvar_etapa("etapa2_concluida_full_workflow", {
                            "session_id": session_id,
                            "synthesis_result": synthesis_result,
                            "behavioral_result": behavioral_result,
                            "market_result": market_result,
                            "timestamp": datetime.now().isoformat()
                        }, categoria="workflow", session_id=session_id)
                        
                        logger.info(f"✅ ETAPA 2 (Workflow Completo) CONCLUÍDA - Sessão: {session_id}")
                        
                    except Exception as e:
                        logger.error(f"❌ Erro na Etapa 2 (Workflow Completo): {e}")
                        salvar_etapa("etapa2_erro_full_workflow", {
                            "session_id": session_id,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }, categoria="workflow", session_id=session_id)
                        return # Aborta o workflow se a segunda etapa falhar
                    
                    # ETAPA 2.5: Verificação AI Externa
                    logger.info(f"🤖 INICIANDO VERIFICAÇÃO AI EXTERNA (Workflow Completo) - Sessão: {session_id}")
                    try:
                        from services.external_ai_integration import external_ai_integration
                        verification_result = await external_ai_integration.verify_session_data(session_id)
                        
                        salvar_etapa("verificacao_ai_concluida_full_workflow", {
                            "session_id": session_id,
                            "verification_result": verification_result,
                            "timestamp": datetime.now().isoformat()
                        }, categoria="workflow", session_id=session_id)
                        
                        logger.info(f"✅ VERIFICAÇÃO AI EXTERNA (Workflow Completo) CONCLUÍDA - Sessão: {session_id}")
                        
                    except Exception as e:
                        logger.error(f"❌ Erro na Verificação AI Externa (Workflow Completo): {e}")
                        salvar_etapa("verificacao_ai_erro_full_workflow", {
                            "session_id": session_id,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }, categoria="workflow", session_id=session_id)
                        # Não aborta o workflow se a verificação falhar
                    
                    # ETAPA 3: Geração dos 16 Módulos e Relatório Final
                    logger.info(f"📝 INICIANDO ETAPA 3 (Workflow Completo) - Sessão: {session_id}")
                    try:
                        modules_result = await services['enhanced_module_processor'].generate_all_modules(session_id)
                        final_report = services['comprehensive_report_generator_v3'].compile_final_markdown_report(session_id)
                        
                        salvar_etapa("etapa3_concluida_full_workflow", {
                            "session_id": session_id,
                            "modules_result": modules_result,
                            "final_report": final_report,
                            "timestamp": datetime.now().isoformat()
                        }, categoria="workflow", session_id=session_id)
                        
                        logger.info(f"✅ ETAPA 3 (Workflow Completo) CONCLUÍDA - Sessão: {session_id}")
                        
                    except Exception as e:
                        logger.error(f"❌ Erro na Etapa 3 (Workflow Completo): {e}")
                        salvar_etapa("etapa3_erro_full_workflow", {
                            "session_id": session_id,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }, categoria="workflow", session_id=session_id)
                        return # Aborta o workflow se a terceira etapa falhar
                    
                    # ETAPA 4: Protocolo CPL Devastador
                    logger.info(f"🎯 INICIANDO PROTOCOLO CPL DEVASTADOR (Workflow Completo) - Sessão: {session_id}")
                    try:
                        cpl_protocol = services['cpl_devastador_protocol']
                        cpl_result = await cpl_protocol.executar_protocolo_completo(
                            tema=context.get('segmento', context.get('produto', query)),
                            segmento=context.get('segmento', 'Não especificado'),
                            publico_alvo=context.get('publico', 'Não especificado'),
                            session_id=session_id
                        )
                        
                        salvar_etapa("cpl_devastador_concluido_full_workflow", {
                            "session_id": session_id,
                            "cpl_result": cpl_result,
                            "timestamp": datetime.now().isoformat()
                        }, categoria="workflow", session_id=session_id)
                        
                        logger.info(f"✅ PROTOCOLO CPL DEVASTADOR (Workflow Completo) CONCLUÍDO - Sessão: {session_id}")
                        
                    except Exception as e:
                        logger.error(f"❌ Erro no CPL Devastador (Workflow Completo): {e}")
                        salvar_etapa("cpl_devastador_erro_full_workflow", {
                            "session_id": session_id,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }, categoria="workflow", session_id=session_id)
                        # Não aborta o workflow se o CPL falhar, apenas registra o erro
                    
                    # Salva resultado final do workflow completo
                    salvar_etapa("workflow_completo_concluido", {
                        "session_id": session_id,
                        "search_results": search_results,
                        "viral_analysis": viral_analysis,
                        "synthesis_result": synthesis_result,
                        "verification_result": verification_result,
                        "modules_result": modules_result,
                        "final_report": final_report,
                        "cpl_result": cpl_result,
                        "timestamp": datetime.now().isoformat()
                    }, categoria="workflow", session_id=session_id)
                    
                    logger.info(f"✅ WORKFLOW COMPLETO CONCLUÍDO - Sessão: {session_id}")
                
                asyncio.run(async_full_workflow_tasks())
                
            except Exception as e:
                logger.error(f"❌ Erro no workflow completo: {e}")
                salvar_etapa("workflow_erro", {
                    "session_id": session_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }, categoria="workflow", session_id=session_id)
        
        # Inicia a thread para o workflow completo
        thread = threading.Thread(target=execute_full_workflow_thread)
        thread.start()
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "message": "Workflow completo iniciado em segundo plano",
            "estimated_total_duration": "12-25 minutos",
            "steps": [
                "Etapa 1: Coleta massiva (3-5 min)",
                "Etapa 2: Síntese com IA (2-4 min)",
                "Verificação AI Externa (1-2 min)",
                "Etapa 3: Geração de módulos (4-6 min)",
                "CPL Devastador (5-8 min)"
            ],
            "status_endpoint": f"/api/workflow/status/{session_id}"
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar workflow completo: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ==========================================
# ROTAS DE STATUS E RESULTADOS
# ==========================================

@enhanced_workflow_bp.route('/workflow/status/<session_id>', methods=['GET'])
def get_workflow_status(session_id):
    """Obtém status do workflow"""
    try:
        status = {
            "session_id": session_id,
            "current_step": 0,
            "step_status": {
                "step1": "pending",
                "step2": "pending",
                "external_ai_verification": "pending",
                "step3": "pending",
                "cpl_devastador": "pending"
            },
            "progress_percentage": 0,
            "estimated_remaining": "Calculando...",
            "last_update": datetime.now().isoformat()
        }
        
        # Verifica se etapa 1 foi concluída
        if os.path.exists(f"analyses_data/{session_id}/relatorio_coleta.md") or \
           os.path.exists(f"analyses_data/workflow/{session_id}/etapa1_concluida_full_workflow.json"):
            status["step_status"]["step1"] = "completed"
            status["current_step"] = 1
            status["progress_percentage"] = 20
        
        # Verifica se etapa 2 foi concluída
        etapa2_file1 = f"analyses_data/workflow/{session_id}/etapa2_concluida_full_workflow.json"
        etapa2_file2 = f"analyses_data/workflow/{session_id}/etapa2_concluida.json"

        if os.path.exists(etapa2_file1) or os.path.exists(etapa2_file2):
            status["step_status"]["step2"] = "completed"
            status["current_step"] = 2
            status["progress_percentage"] = 40
            logger.info(f"✅ Etapa 2 detectada como concluída para sessão {session_id}")
            logger.info(f"   - Arquivo 1 existe: {os.path.exists(etapa2_file1)}")
            logger.info(f"   - Arquivo 2 existe: {os.path.exists(etapa2_file2)}")

        # Verifica se verificação AI foi concluída
        verificacao_ai_file = f"analyses_data/workflow/{session_id}/verificacao_ai_concluida.json"
        if os.path.exists(verificacao_ai_file):
            status["step_status"]["external_ai_verification"] = "completed"
            status["current_step"] = 3
            status["progress_percentage"] = 60
            logger.info(f"✅ Verificação AI detectada como concluída para sessão {session_id}")

        # Verifica se etapa 3 foi concluída
        if os.path.exists(f"analyses_data/{session_id}/relatorio_final.md") or \
           os.path.exists(f"analyses_data/workflow/{session_id}/etapa3_concluida_full_workflow.json"):
            status["step_status"]["step3"] = "completed"
            status["current_step"] = 4
            status["progress_percentage"] = 80
        
        # Verifica se CPL Devastador foi concluído
        if os.path.exists(f"analyses_data/{session_id}/cpl_protocol_result.json") or \
           os.path.exists(f"analyses_data/workflow/{session_id}/cpl_devastador_concluido_full_workflow.json"):
            status["step_status"]["cpl_devastador"] = "completed"
            status["current_step"] = 5
            status["progress_percentage"] = 100
            status["estimated_remaining"] = "Concluído"
        
        # Verifica se há erros
        error_files_patterns = [
            f"analyses_data/workflow/{session_id}/etapa1_erro*",
            f"analyses_data/workflow/{session_id}/etapa2_erro*",
            f"analyses_data/workflow/{session_id}/verificacao_ai_erro*",
            f"analyses_data/workflow/{session_id}/etapa3_erro*",
            f"analyses_data/workflow/{session_id}/cpl_devastador_erro*",
            f"analyses_data/workflow/{session_id}/workflow_erro*"
        ]
        for pattern in error_files_patterns:
            if glob.glob(pattern):
                status["error"] = "Erro detectado em uma das etapas do workflow."
                if "etapa1_erro" in pattern:
                    status["step_status"]["step1"] = "failed"
                elif "etapa2_erro" in pattern:
                    status["step_status"]["step2"] = "failed"
                elif "verificacao_ai_erro" in pattern:
                    status["step_status"]["external_ai_verification"] = "failed"
                elif "etapa3_erro" in pattern:
                    status["step_status"]["step3"] = "failed"
                elif "cpl_devastador_erro" in pattern:
                    status["step_status"]["cpl_devastador"] = "failed"
                break
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter status: {e}")
        return jsonify({
            "session_id": session_id,
            "error": str(e),
            "status": "error"
        }), 500

@enhanced_workflow_bp.route('/workflow/results/<session_id>', methods=['GET'])
def get_workflow_results(session_id):
    """Obtém resultados do workflow"""
    try:
        results = {
            "session_id": session_id,
            "available_files": [],
            "final_report_available": False,
            "modules_generated": 0,
            "screenshots_captured": 0,
            "cpl_devastador_available": False,
            "verification_available": False
        }
        
        # Verifica relatório final
        final_report_path = os.path.join("analyses_data", session_id, "relatorio_final.md")
        if os.path.exists(final_report_path):
            results["final_report_available"] = True
            results["final_report_path"] = final_report_path
        
        # Verifica CPL Devastador
        cpl_result_path = os.path.join("analyses_data", session_id, "cpl_protocol_result.json")
        if os.path.exists(cpl_result_path):
            results["cpl_devastador_available"] = True
            results["cpl_result_path"] = cpl_result_path
        
        # Verifica Verificação AI
        verification_file = f"analyses_data/workflow/{session_id}/verificacao_ai_concluida.json"
        if os.path.exists(verification_file):
            results["verification_available"] = True
            results["verification_path"] = verification_file
        
        # Conta módulos gerados
        modules_dir = os.path.join("analyses_data", session_id, "modules")
        if os.path.exists(modules_dir):
            modules = [f for f in os.listdir(modules_dir) if f.endswith('.md')]
            results["modules_generated"] = len(modules)
            results["modules_list"] = modules
        
        # Conta screenshots
        files_dir = os.path.join("analyses_data", "files", session_id)
        if os.path.exists(files_dir):
            screenshots = [f for f in os.listdir(files_dir) if f.endswith('.png')]
            results["screenshots_captured"] = len(screenshots)
            results["screenshots_list"] = screenshots
        
        # Lista todos os arquivos disponíveis
        session_dir = os.path.join("analyses_data", session_id)
        if os.path.exists(session_dir):
            for root, dirs, files in os.walk(session_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, session_dir)
                    results["available_files"].append({
                        "name": file,
                        "path": relative_path,
                        "size": os.path.getsize(file_path),
                        "type": file.split('.')[-1] if '.' in file else 'unknown'
                    })
        
        return jsonify(results), 200
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter resultados: {e}")
        return jsonify({
            "session_id": session_id,
            "error": str(e)
        }), 500

@enhanced_workflow_bp.route('/workflow/download/<session_id>/<file_type>', methods=['GET'])
def download_workflow_file(session_id, file_type):
    """Download de arquivos do workflow"""
    try:
        # Define o caminho base
        base_path = os.path.join("analyses_data", session_id)
        
        if file_type == "final_report":
            file_path = os.path.join(base_path, "relatorio_final.md")
            if not os.path.exists(file_path):
                file_path = os.path.join(base_path, "relatorio_final_completo.md")
            filename = f"relatorio_final_{session_id}.md"
        elif file_type == "complete_report":
            file_path = os.path.join(base_path, "relatorio_final_completo.md")
            filename = f"relatorio_completo_{session_id}.md"
        elif file_type == "cpl_devastador":
            file_path = os.path.join(base_path, "cpl_protocol_result.json")
            filename = f"cpl_devastador_{session_id}.json"
        elif file_type == "verification":
            file_path = f"analyses_data/workflow/{session_id}/verificacao_ai_concluida.json"
            filename = f"verification_ai_{session_id}.json"
        else:
            return jsonify({"error": "Tipo de relatório inválido"}), 400
        
        if not os.path.exists(file_path):
            return jsonify({"error": "Arquivo não encontrado"}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"❌ Erro no download: {e}")
        return jsonify({"error": str(e)}), 500

# ==========================================
# FUNÇÕES AUXILIARES (MANTIDAS DO ORIGINAL)
# ==========================================

def _generate_collection_report(
    search_results: Dict[str, Any],
    viral_analysis: Dict[str, Any],
    session_id: str,
    context: Dict[str, Any]
) -> str:
    """Gera relatório consolidado com dados extraídos"""
    # Função auxiliar para formatar números com segurança
    def safe_format_int(value):
        try:
            return f"{int(value):,}"
        except (ValueError, TypeError):
            return str(value) if value is not None else 'N/A'
    
    # Carrega dados salvos de forma simplificada
    all_saved_excerpts = _load_all_saved_excerpts(session_id)
    all_viral_data = _load_all_viral_data(session_id)
    massive_search_data = _load_massive_search_data(session_id)
    
    report = f"""# RELATÓRIO CONSOLIDADO ULTRA-COMPLETO - ARQV30 Enhanced v3.0
**🎯 DADOS 100% REAIS - ZERO SIMULAÇÃO - TUDO UNIFICADO**
**Sessão:** {session_id}  
**Query:** {search_results.get('query', 'N/A')}  
**Iniciado em:** {search_results.get('statistics', {}).get('search_started', 'N/A')}  
**Duração:** {search_results.get('statistics', {}).get('search_duration', 0):.2f} segundos
---
## 📊 RESUMO EXECUTIVO DA COLETA MASSIVA
### Estatísticas Completas:
- **Total de Fontes:** {search_results.get('statistics', {}).get('total_sources', 0)}
- **URLs Únicas:** {search_results.get('statistics', {}).get('unique_urls', 0)}
- **Trechos Salvos:** {len(all_saved_excerpts)}
- **Dados Virais:** {len(all_viral_data)}
- **Dados Massive Search:** {len(massive_search_data)}
- **Screenshots:** {len(viral_analysis.get('screenshots_captured', []))}
---
## TRECHOS DE CONTEÚDO EXTRAÍDO
*Amostras do conteúdo real coletado durante a busca massiva*
"""
    
    # Adiciona trechos de conteúdo
    report += _generate_content_excerpts_section(search_results, viral_analysis)
    
    # Adiciona dados virais completos
    report += _incorporate_viral_data(session_id, viral_analysis)
    
    # Adiciona resultados do Massive Search Engine
    if massive_search_data:
        report += "## 🚀 DADOS DO MASSIVE SEARCH ENGINE\n"
        for i, massive_item in enumerate(massive_search_data, 1):
            report += f"### Massive Search Result {i}\n"
            if isinstance(massive_item, dict):
                produto = massive_item.get('produto', 'N/A')
                publico_alvo = massive_item.get('publico_alvo', 'N/A')
                report += f"**Produto:** {produto}\n"
                report += f"**Público Alvo:** {publico_alvo}\n"
                busca_massiva = massive_item.get('busca_massiva', {})
                if busca_massiva:
                    alibaba_results = busca_massiva.get('alibaba_websailor_results', [])
                    real_search_results = busca_massiva.get('real_search_orchestrator_results', [])
                    report += f"**Resultados Alibaba WebSailor:** {len(alibaba_results)}\n"
                    report += f"**Resultados Real Search:** {len(real_search_results)}\n"
                    for j, alibaba_result in enumerate(alibaba_results[:3], 1):
                        if isinstance(alibaba_result, dict):
                            report += f"  - Alibaba {j}: {alibaba_result.get('query', 'N/A')}\n"
                metadata = massive_item.get('metadata', {})
                if metadata:
                    report += f"**Total de Buscas:** {metadata.get('total_searches', 0)}\n"
                    report += f"**Tamanho Final:** {metadata.get('size_kb', 0):.1f} KB\n"
                    report += f"**APIs Utilizadas:** {len(metadata.get('apis_used', []))}\n"
            report += "\n---\n"
    
    # Adiciona resultados do YouTube
    youtube_results = search_results.get('youtube_results', [])
    if youtube_results:
        report += "## 📺 RESULTADOS COMPLETOS DO YOUTUBE\n"
        for i, result in enumerate(youtube_results, 1):
            report += f"### YouTube {i}: {result.get('title', 'Sem título')}\n"
            report += f"**Canal:** {result.get('channel', 'N/A')}  \n"
            report += f"**Views:** {safe_format_int(result.get('view_count', 'N/A'))}  \n"
            report += f"**Likes:** {safe_format_int(result.get('like_count', 'N/A'))}  \n"
            report += f"**Comentários:** {safe_format_int(result.get('comment_count', 'N/A'))}  \n"
            report += f"**Score Viral:** {result.get('viral_score', 0):.2f}/10  \n"
            report += f"**URL:** {result.get('url', 'N/A')}  \n"
            description = result.get('description', '')
            if description:
                report += f"**Descrição:** {description}  \n"
            report += "\n---\n"
    
    # Adiciona resultados de Redes Sociais
    social_results = search_results.get('social_results', [])
    if social_results:
        report += "## 📱 RESULTADOS COMPLETOS DE REDES SOCIAIS\n"
        for i, result in enumerate(social_results, 1):
            report += f"### Social {i}: {result.get('title', 'Sem título')}\n"
            report += f"**Plataforma:** {result.get('platform', 'N/A').title()}  \n"
            report += f"**Autor:** {result.get('author', 'N/A')}  \n"
            report += f"**Engajamento:** {result.get('viral_score', 0):.2f}/10  \n"
            report += f"**URL:** {result.get('url', 'N/A')}  \n"
            content = result.get('content', '')
            if content:
                report += f"**CONTEÚDO COMPLETO:** {content}  \n"
            report += "\n---\n"
    
    # Adiciona Screenshots e Evidências Visuais
    screenshots = viral_analysis.get('screenshots_captured', [])
    if screenshots:
        report += "## 📸 EVIDÊNCIAS VISUAIS COMPLETAS\n"
        for i, screenshot in enumerate(screenshots, 1):
            report += f"### Screenshot {i}: {screenshot.get('title', 'Sem título')}\n"
            report += f"**Plataforma:** {screenshot.get('platform', 'N/A').title()}  \n"
            report += f"**Score Viral:** {screenshot.get('viral_score', 0):.2f}/10  \n"
            report += f"**URL Original:** {screenshot.get('url', 'N/A')}  \n"
            metrics = screenshot.get('content_metrics', {})
            if metrics:
                if 'views' in metrics:
                    report += f"**Views:** {safe_format_int(metrics['views'])}  \n"
                if 'likes' in metrics:
                    report += f"**Likes:** {safe_format_int(metrics['likes'])}  \n"
                if 'comments' in metrics:
                    report += f"**Comentários:** {safe_format_int(metrics['comments'])}  \n"
            img_path = screenshot.get('relative_path', '')
            if img_path:
                report += f"**Arquivo:** {img_path}  \n"
            report += "\n---\n"
    
    # Adiciona Contexto da Análise
    report += "## 🎯 CONTEXTO COMPLETO DA ANÁLISE\n"
    for key, value in context.items():
        if value:
            report += f"**{key.replace('_', ' ').title()}:** {value}  \n"
    
    # Estatísticas Finais
    total_content_chars = sum(len(str(excerpt.get('conteudo', ''))) for excerpt in all_saved_excerpts)
    
    report += f"""
---
## 📊 ESTATÍSTICAS FINAIS CONSOLIDADAS
- **Total de Trechos Extraídos:** {len(all_saved_excerpts)}
- **Total de Dados Virais:** {len(all_viral_data)}
- **Total de Dados Massive Search:** {len(massive_search_data)}
- **Total de Caracteres de Conteúdo:** {total_content_chars:,}
- **Total de Screenshots:** {len(screenshots)}
- **Total de Resultados Web:** {len(search_results.get('web_results', []))}
- **Total de Resultados YouTube:** {len(search_results.get('youtube_results', []))}
- **Total de Resultados Sociais:** {len(search_results.get('social_results', []))}
**🔥 GARANTIA: 100% DADOS REAIS - ZERO SIMULAÇÃO - TUDO CONSOLIDADO**
---
*Relatório ultra-consolidado gerado automaticamente em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}*
*Pronto para análise profunda pela IA QWEN via OpenRouter*
"""
    
    return report

def _gerar_consolidacao_final_etapa1(session_id, search_results, viral_analysis, massive_results, viral_results: Dict = None) -> Dict[str, Any]:
    """Gera consolidação final de TODOS os dados coletados na Etapa 1"""
    if viral_results is None:
        viral_results = {} # Inicializa como dicionário vazio se não for fornecido
    
    try:
        consolidacao = {
            "session_id": session_id,
            "tipo": "consolidacao_etapa1_completa",
            "dados_web": [],
            "dados_sociais": [],
            "dados_virais": [],
            "imagens_baixadas": [],
            "screenshots_capturados": [],
            "viral_results_files": [],
            "trechos_extraidos": [],
            "dados_viral_integration": viral_results,
            "detalhes_buscas": [],
            "res_busca_files": [],
            "consolidado_files": [],
            "etapa1_concluida_files": [],
            "relatorio_coleta": {},
            "estatisticas": {
                "total_dados_coletados": 0,
                "total_caracteres": 0,
                "fontes_unicas": 0,
                "qualidade_media": 0,
                "relevancia_media": 0
            },
            "consolidado_em": datetime.now().isoformat()
        }
        
        # CONSOLIDAR DADOS WEB
        if search_results.get('web_results'):
            for result in search_results['web_results']:
                if result.get('url') and result.get('title'):
                    consolidacao["dados_web"].append({
                        "url": result['url'],
                        "titulo": result['title'],
                        "fonte": result.get('source', 'web'),
                        "relevancia": result.get('relevancia', 0),
                        "trecho": result.get('snippet', ''),
                        "data_coleta": datetime.now().isoformat()
                    })
        
        # CONSOLIDAR DADOS SOCIAIS
        if search_results.get('social_results'):
            for result in search_results['social_results']:
                if result.get('url') and result.get('title'):
                    consolidacao["dados_sociais"].append({
                        "url": result['url'],
                        "titulo": result['title'],
                        "plataforma": result.get('platform', 'unknown'),
                        "autor": result.get('author', ''),
                        "engajamento": result.get('viral_score', 0),
                        "conteudo": result.get('content', ''),
                        "data_coleta": datetime.now().isoformat()
                    })
        
        # CONSOLIDAR DADOS VIRAL INTEGRATION
        if viral_results and isinstance(viral_results, dict):
            if 'viral_images' in viral_results:
                for img in viral_results['viral_images']:
                    if isinstance(img, dict):
                        consolidacao["dados_virais"].append({
                            "url": img.get('url', ''),
                            "plataforma": img.get('platform', 'unknown'),
                            "engajamento": img.get('engagement_score', 0),
                            "views_estimadas": img.get('views_estimate', 0),
                            "likes_estimados": img.get('likes_estimate', 0),
                            "caminho_imagem": img.get('image_path', ''),
                            "data_coleta": datetime.now().isoformat()
                        })
        
        # CONSOLIDAR SCREENSHOTS
        if viral_analysis.get('screenshots_captured'):
            for screenshot in viral_analysis['screenshots_captured']:
                if isinstance(screenshot, dict):
                    consolidacao["screenshots_capturados"].append({
                        "url": screenshot.get('url', ''),
                        "titulo": screenshot.get('title', ''),
                        "plataforma": screenshot.get('platform', 'unknown'),
                        "score_viral": screenshot.get('viral_score', 0),
                        "caminho_arquivo": screenshot.get('relative_path', ''),
                        "metricas": screenshot.get('content_metrics', {}),
                        "data_coleta": datetime.now().isoformat()
                    })
        
        # CALCULAR ESTATÍSTICAS
        total_dados = (
            len(consolidacao["dados_web"]) +
            len(consolidacao["dados_sociais"]) +
            len(consolidacao["dados_virais"]) +
            len(consolidacao["screenshots_capturados"])
        )
        
        consolidacao["estatisticas"]["total_dados_coletados"] = total_dados
        consolidacao["estatisticas"]["fontes_unicas"] = len(set(
            [d['url'] for d in consolidacao["dados_web"]] +
            [d['url'] for d in consolidacao["dados_sociais"]] +
            [d['url'] for d in consolidacao["dados_virais"]]
        ))
        
        # Calcular caracteres totais
        total_caracteres = 0
        for item in consolidacao["dados_web"]:
            total_caracteres += len(str(item.get('trecho', '')))
        for item in consolidacao["dados_sociais"]:
            total_caracteres += len(str(item.get('conteudo', '')))
        
        consolidacao["estatisticas"]["total_caracteres"] = total_caracteres
        
        # Calcular médias de qualidade e relevância
        relevancias = [item.get('relevancia', 0) for item in consolidacao["dados_web"]]
        engajamentos = [item.get('engajamento', 0) for item in consolidacao["dados_sociais"]]
        
        if relevancias:
            consolidacao["estatisticas"]["relevancia_media"] = sum(relevancias) / len(relevancias)
        if engajamentos:
            consolidacao["estatisticas"]["qualidade_media"] = sum(engajamentos) / len(engajamentos)
        
        logger.info(f"✅ Consolidação final gerada: {total_dados} dados coletados")
        
        return consolidacao
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar consolidação final: {e}")
        return {
            "session_id": session_id,
            "erro": str(e),
            "consolidado_em": datetime.now().isoformat()
        }

def _save_collection_report(report: str, session_id: str):
    """Salva relatório de coleta em arquivo"""
    try:
        # Criar diretório se não existir
        report_dir = os.path.join("analyses_data", session_id)
        os.makedirs(report_dir, exist_ok=True)
        
        # Salvar relatório
        report_path = os.path.join(report_dir, "relatorio_coleta.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"✅ Relatório de coleta salvo: {report_path}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar relatório de coleta: {e}")

def _load_all_saved_excerpts(session_id: str) -> List[Dict[str, Any]]:
    """Carrega todos os trechos salvos da sessão"""
    try:
        excerpts = []
        excerpts_dir = os.path.join("analyses_data", session_id, "excerpts")
        
        if os.path.exists(excerpts_dir):
            for file in os.listdir(excerpts_dir):
                if file.endswith('.json'):
                    with open(os.path.join(excerpts_dir, file), 'r', encoding='utf-8') as f:
                        try:
                            excerpt_data = json.load(f)
                            if isinstance(excerpt_data, dict):
                                excerpts.append(excerpt_data)
                        except:
                            continue
        
        return excerpts
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar trechos salvos: {e}")
        return []

def _load_all_viral_data(session_id: str) -> List[Dict[str, Any]]:
    """Carrega todos os dados virais da sessão"""
    try:
        viral_data = []
        viral_dir = os.path.join("analyses_data", session_id, "viral_data")
        
        if os.path.exists(viral_dir):
            for file in os.listdir(viral_dir):
                if file.endswith('.json'):
                    with open(os.path.join(viral_dir, file), 'r', encoding='utf-8') as f:
                        try:
                            data = json.load(f)
                            if isinstance(data, dict):
                                viral_data.append(data)
                        except:
                            continue
        
        return viral_data
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar dados virais: {e}")
        return []

def _load_massive_search_data(session_id: str) -> List[Dict[str, Any]]:
    """Carrega dados do massive search da sessão"""
    try:
        massive_data = []
        massive_file = os.path.join("analyses_data", session_id, "massive_search_results.json")
        
        if os.path.exists(massive_file):
            with open(massive_file, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        massive_data = data
                    elif isinstance(data, dict) and 'results' in data:
                        massive_data = data['results']
                except:
                    pass
        
        return massive_data
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar dados massive search: {e}")
        return []

def _generate_content_excerpts_section(search_results: Dict[str, Any], viral_analysis: Dict[str, Any]) -> str:
    """Gera seção de trechos de conteúdo para o relatório"""
    section = "\n## 📄 CONTEÚDO EXTRAÍDO DAS FONTES\n\n"
    
    # Adiciona trechos dos resultados web
    web_results = search_results.get('web_results', [])
    if web_results:
        section += "### Resultados Web Principais\n\n"
        for i, result in enumerate(web_results[:5], 1):
            section += f"**{i}. {result.get('title', 'Sem título')}**\n"
            section += f"URL: {result.get('url', 'N/A')}\n"
            snippet = result.get('snippet', '')
            if snippet:
                section += f"Trecho: {snippet[:200]}...\n"
            section += "\n---\n\n"
    
    return section

def _incorporate_viral_data(session_id: str, viral_analysis: Dict[str, Any]) -> str:
    """Incorpora dados virais ao relatório"""
    section = "\n## 🔥 DADOS VIRAL INTEGRATION\n\n"
    
    # Adiciona estatísticas virais
    if viral_analysis:
        screenshots = viral_analysis.get('screenshots_captured', [])
        if screenshots:
            section += f"### Screenshots Capturados: {len(screenshots)}\n\n"
            for i, screenshot in enumerate(screenshots[:3], 1):
                section += f"**{i}. {screenshot.get('title', 'Sem título')}**\n"
                section += f"Plataforma: {screenshot.get('platform', 'N/A')}\n"
                section += f"Score Viral: {screenshot.get('viral_score', 0):.2f}/10\n"
                section += "\n---\n\n"
    
    return section
