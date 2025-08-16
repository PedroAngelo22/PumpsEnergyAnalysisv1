import streamlit as st
import pandas as pd
from fpdf import FPDF
import math
import time

# --- Dicionário de Fluidos com suas propriedades (Massa Específica e Viscosidade Cinemática) ---
# Massa Específica (rho) em kg/m³
# Viscosidade Cinemática (nu) em m²/s
FLUIDOS = {
    "Água a 20°C": {"rho": 998.2, "nu": 1.004e-6},
    "Etanol a 20°C": {"rho": 789.0, "nu": 1.51e-6},
    "Glicerina a 20°C": {"rho": 1261.0, "nu": 1.49e-3},
    "Óleo Leve (genérico)": {"rho": 880.0, "nu": 1.5e-5}
}

# --- Funções de Cálculo de Engenharia ---

def calcular_perda_carga(vazao_m3h, diametro_mm, comprimento_m, rugosidade_mm, k_total, fluido_selecionado):
    """Calcula a perda de carga usando a equação de Darcy-Weisbach."""
    # Conversões
    vazao_m3s = vazao_m3h / 3600
    diametro_m = diametro_mm / 1000
    rugosidade_m = rugosidade_mm / 1000
    
    # Propriedades do fluido
    rho = FLUIDOS[fluido_selecionado]["rho"]
    nu = FLUIDOS[fluido_selecionado]["nu"]
    
    # Cálculos intermediários
    area = (math.pi * diametro_m**2) / 4
    if area == 0: return 0, 0
    velocidade = vazao_m3s / area
    
    # Número de Reynolds
    reynolds = (velocidade * diametro_m) / nu if nu > 0 else 0
    
    # Fator de atrito (f) - Usando a fórmula explícita de Swamee-Jain
    # Válida para 5000 < Re < 10^8 e 10^-6 < e/D < 10^-2
    if reynolds > 4000: # Regime turbulento
        fator_atrito = 0.25 / (math.log10((rugosidade_m / (3.7 * diametro_m)) + (5.74 / reynolds**0.9)))**2
    else: # Regime laminar (aproximação)
        fator_atrito = 64 / reynolds if reynolds > 0 else 0
        
    # Perda de carga principal (atrito na tubulação)
    perda_carga_principal = fator_atrito * (comprimento_m / diametro_m) * (velocidade**2 / (2 * 9.81))
    
    # Perda de carga localizada (acessórios)
    perda_carga_localizada = k_total * (velocidade**2 / (2 * 9.81))
    
    return perda_carga_principal, perda_carga_localizada

def calcular_analise_energetica(vazao_m3h, h_man, eficiencia_bomba, eficiencia_motor, horas_dia, custo_kwh, fluido_selecionado):
    """Realiza todos os cálculos de potência, consumo e custo."""
    rho = FLUIDOS[fluido_selecionado]["rho"]
    g = 9.81
    vazao_m3s = vazao_m3h / 3600

    potencia_hidraulica_W = vazao_m3s * rho * g * h_man
    potencia_eixo_W = potencia_hidraulica_W / eficiencia_bomba if eficiencia_bomba > 0 else 0
    potencia_eletrica_W = potencia_eixo_W / eficiencia_motor if eficiencia_motor > 0 else 0
    
    potencia_eletrica_kW = potencia_eletrica_W / 1000
    
    consumo_diario_kWh = potencia_eletrica_kW * horas_dia
    consumo_mensal_kWh = consumo_diario_kWh * 30
    
    custo_mensal = consumo_mensal_kWh * custo_kwh
    custo_anual = custo_mensal * 12

    return {
        "potencia_hidraulica_kW": potencia_hidraulica_W / 1000,
        "potencia_eixo_kW": potencia_eixo_W / 1000,
        "potencia_eletrica_kW": potencia_eletrica_kW,
        "consumo_mensal_kWh": consumo_mensal_kWh,
        "custo_mensal": custo_mensal,
        "custo_anual": custo_anual
    }

def gerar_sugestoes(eficiencia_bomba, eficiencia_motor, custo_anual):
    """Gera uma lista de sugestões de melhoria."""
    sugestoes = []
    if eficiencia_bomba < 0.6:
        sugestoes.append("Eficiência da bomba abaixo de 60%. Considere a substituição por um modelo mais moderno e eficiente.")
    if eficiencia_motor < 0.85:
        sugestoes.append("Eficiência do motor abaixo de 85%. Motores de alto rendimento (IR3+) podem gerar grande economia.")
    if custo_anual > 5000:
        sugestoes.append("Se a vazão for variável, um inversor de frequência pode reduzir drasticamente o consumo de energia.")
    sugestoes.append("Realize manutenções preventivas, verifique vazamentos e o estado dos rotores e selos da bomba.")
    return sugestoes

# --- Função para Geração de PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Relatório de Análise Energética de Bombeamento', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')
        
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 11)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)

    def chapter_body(self, data):
        self.set_font('Arial', '', 10)
        for key, value in data.items():
            self.cell(80, 7, f"  {key}:", 0, 0)
            self.cell(0, 7, str(value), 0, 1)
        self.ln(5)

def criar_relatorio_pdf(inputs, resultados, sugestoes):
    pdf = PDF()
    pdf.add_page()
    
    pdf.chapter_title("Parâmetros de Entrada")
    pdf.chapter_body(inputs)
    
    pdf.chapter_title("Resultados da Análise")
    pdf.chapter_body(resultados)
    
    pdf.chapter_title("Sugestões de Melhoria")
    pdf.set_font('Arial', '', 10)
    for i, sugestao in enumerate(sugestoes):
        pdf.multi_cell(0, 5, f"- {sugestao}")
        pdf.ln(2)
        
    return pdf.output()

# --- Interface do Aplicativo Streamlit ---

st.set_page_config(layout="wide", page_title="Análise de Sistemas de Bombeamento")
st.title("💧 Análise Avançada de Sistemas de Bombeamento")

# --- Barra Lateral para Entradas ---
with st.sidebar:
    st.header("⚙️ Parâmetros do Sistema")
    
    fluido_selecionado = st.selectbox("Selecione o Fluido", list(FLUIDOS.keys()))
    vazao = st.number_input("Vazão Desejada (m³/h)", min_value=0.1, value=50.0, step=1.0)
    
    tipo_calculo_h = st.radio("Cálculo da Altura Manométrica", 
                             ["Informar manualmente", "Calcular a partir da tubulação"],
                             key="tipo_h")
    
    h_man_total = 0
    if tipo_calculo_h == "Informar manualmente":
        h_man_total = st.number_input("Altura Manométrica Total (m)", min_value=1.0, value=30.0, step=0.5)
    else:
        with st.expander("Dados para Cálculo da Perda de Carga"):
            h_geometrica = st.number_input("Altura Geométrica (desnível) (m)", min_value=0.0, value=15.0)
            comp_tub = st.number_input("Comprimento da Tubulação (m)", min_value=1.0, value=100.0)
            diam_tub = st.number_input("Diâmetro Interno da Tubulação (mm)", min_value=1.0, value=100.0)
            rug_tub = st.number_input("Rugosidade do Material (mm)", min_value=0.001, value=0.15, format="%.3f")
            k_total_acessorios = st.number_input("Soma dos Coeficientes de Perda (K) dos Acessórios", min_value=0.0, value=5.0)
            
    st.header("🔧 Eficiência dos Equipamentos")
    rend_bomba = st.slider("Eficiência da Bomba (%)", 10, 100, 70)
    rend_motor = st.slider("Eficiência do Motor (%)", 50, 100, 90)
    
    st.header("🗓️ Operação e Custo")
    horas_por_dia = st.number_input("Horas de Operação por Dia", 1.0, 24.0, 8.0, 0.5)
    tarifa_energia = st.number_input("Custo da Energia (R$/kWh)", 0.10, 2.00, 0.75, 0.01, format="%.2f")

# --- Lógica Principal e Exibição de Resultados ---
col1, col2 = st.columns([0.6, 0.4])

with col1:
    st.header("📊 Resultados da Análise")
    
    # Cálculos
    if tipo_calculo_h == "Calcular a partir da tubulação":
        pc_p, pc_l = calcular_perda_carga(vazao, diam_tub, comp_tub, rug_tub, k_total_acessorios, fluido_selecionado)
        h_man_total = h_geometrica + pc_p + pc_l
        
        st.subheader("Altura Manométrica Calculada")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Altura Geométrica", f"{h_geometrica:.2f} m")
        c2.metric("Perda Principal", f"{pc_p:.2f} m")
        c3.metric("Perda Localizada", f"{pc_l:.2f} m")
        c4.metric("ALTURA TOTAL", f"{h_man_total:.2f} m", delta="Calculado")
    
    resultados = calcular_analise_energetica(vazao, h_man_total, rend_bomba/100, rend_motor/100, horas_por_dia, tarifa_energia, fluido_selecionado)

    st.subheader("Potências e Custos")
    c1, c2, c3 = st.columns(3)
    c1.metric("Potência Elétrica", f"{resultados['potencia_eletrica_kW']:.2f} kW")
    c2.metric("Custo Mensal", f"R$ {resultados['custo_mensal']:.2f}")
    c3.metric("Custo Anual", f"R$ {resultados['custo_anual']:.2f}")

    st.subheader("Gráfico: Custo Anual vs. Horas de Operação")
    horas_range = range(1, 25)
    custos_range = [calcular_analise_energetica(vazao, h_man_total, rend_bomba/100, rend_motor/100, h, tarifa_energia, fluido_selecionado)['custo_anual'] for h in horas_range]
    chart_data = pd.DataFrame({'Horas de Operação por Dia': horas_range, 'Custo Anual (R$)': custos_range})
    st.line_chart(chart_data.set_index('Horas de Operação por Dia'))

with col2:
    st.header("💡 Sugestões e Relatório")
    sugestoes = gerar_sugestoes(rend_bomba/100, rend_motor/100, resultados['custo_anual'])
    for sugestao in sugestoes:
        st.info(sugestao)
    
    st.header("📄 Gerar Relatório")
    
    # Coletando inputs para o relatório
    inputs_relatorio = {
        "Fluido": fluido_selecionado,
        "Vazão": f"{vazao} m³/h",
        "Altura Manométrica Total": f"{h_man_total:.2f} m",
        "Eficiência da Bomba": f"{rend_bomba}%",
        "Eficiência do Motor": f"{rend_motor}%",
        "Horas/Dia": f"{horas_por_dia} h",
        "Tarifa": f"R$ {tarifa_energia:.2f}/kWh"
    }
    resultados_relatorio = {
        "Potência Elétrica Consumida": f"{resultados['potencia_eletrica_kW']:.2f} kW",
        "Consumo Mensal": f"{resultados['consumo_mensal_kWh']:.0f} kWh",
        "Custo Mensal": f"R$ {resultados['custo_mensal']:.2f}",
        "Custo Anual": f"R$ {resultados['custo_anual']:.2f}"
    }

    pdf_bytes = criar_relatorio_pdf(inputs_relatorio, resultados_relatorio, sugestoes)
    
    # Timestamp para nome do arquivo
    timestr = time.strftime("%Y%m%d-%H%M%S")
    
    st.download_button(
        label="Download do Relatório em PDF",
        data=pdf_bytes,
        file_name=f"Relatorio_Bombeamento_{timestr}.pdf",
        mime="application/octet-stream"
    )
