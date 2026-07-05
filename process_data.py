"""
Script para processar dados extraídos do Clinicys
Limpa, estrutura e prepara para alimentar a planilha Excel
"""

import pandas as pd
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataProcessor:
    def __init__(self):
        """Inicializar o processador de dados"""
        self.df = None
        logger.info("DataProcessor inicializado")

    def load_data(self, csv_file):
        """
        Carregar dados do arquivo CSV
        
        Args:
            csv_file: Caminho do arquivo CSV
        """
        try:
            self.df = pd.read_csv(csv_file, encoding="utf-8-sig")
            logger.info(f"Dados carregados: {len(self.df)} registros")
            return self.df
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {str(e)}")
            raise

    def clean_phone(self, phone):
        """
        Limpar número de telefone
        Remove caracteres especiais, mantém apenas números
        """
        if pd.isna(phone):
            return None
        
        phone_str = str(phone).strip()
        # Remove todos os caracteres não numéricos
        phone_clean = ''.join(filter(str.isdigit, phone_str))
        
        return phone_clean if phone_clean else None

    def clean_data(self):
        """Limpar e estruturar os dados"""
        try:
            if self.df is None:
                raise ValueError("Dados não carregados. Execute load_data() primeiro.")
            
            # Renomear colunas para padronizar
            column_mapping = {
                'Data do Atendimento': 'data_atendimento',
                'Paciente': 'nome_paciente',
                'Prontuário': 'id_paciente',
                'Procedimento': 'procedimento',
                'Médico': 'medico',
            }
            
            # Aplicar mapeamento (se as colunas existem)
            for original, novo in column_mapping.items():
                if original in self.df.columns:
                    self.df.rename(columns={original: novo}, inplace=True)
            
            # Converter datas para formato padronizado
            if 'data_atendimento' in self.df.columns:
                self.df['data_atendimento'] = pd.to_datetime(
                    self.df['data_atendimento'], 
                    format='%d/%m/%Y',
                    errors='coerce'
                )
            
            # Limpar nomes (título case)
            if 'nome_paciente' in self.df.columns:
                self.df['nome_paciente'] = self.df['nome_paciente'].str.title()
            
            # Limpar telefones
            if 'telefone' in self.df.columns:
                self.df['telefone'] = self.df['telefone'].apply(self.clean_phone)
            
            # Remover linhas completamente vazias
            self.df.dropna(how='all', inplace=True)
            
            # Remover duplicatas
            self.df.drop_duplicates(inplace=True)
            
            logger.info(f"Dados limpos: {len(self.df)} registros após limpeza")
            return self.df
            
        except Exception as e:
            logger.error(f"Erro ao limpar dados: {str(e)}")
            raise

    def validate_data(self):
        """Validar integridade dos dados"""
        try:
            issues = []
            
            # Verificar campos obrigatórios
            required_fields = ['id_paciente', 'nome_paciente', 'medico']
            for field in required_fields:
                if field not in self.df.columns:
                    issues.append(f"Campo obrigatório faltando: {field}")
            
            # Verificar valores nulos em campos críticos
            for field in ['nome_paciente', 'medico']:
                if field in self.df.columns:
                    null_count = self.df[field].isna().sum()
                    if null_count > 0:
                        issues.append(f"Campo '{field}' tem {null_count} valores nulos")
            
            if issues:
                logger.warning("Problemas encontrados:")
                for issue in issues:
                    logger.warning(f"  - {issue}")
            else:
                logger.info("Validação passou: sem problemas encontrados")
            
            return issues
            
        except Exception as e:
            logger.error(f"Erro ao validar dados: {str(e)}")
            raise

    def get_summary(self):
        """Gerar sumário dos dados extraídos"""
        try:
            summary = {
                'total_registros': len(self.df),
                'medicos_unicos': self.df['medico'].nunique() if 'medico' in self.df.columns else 0,
                'pacientes_unicos': self.df['nome_paciente'].nunique() if 'nome_paciente' in self.df.columns else 0,
                'data_minima': self.df['data_atendimento'].min() if 'data_atendimento' in self.df.columns else None,
                'data_maxima': self.df['data_atendimento'].max() if 'data_atendimento' in self.df.columns else None,
            }
            
            logger.info("=== SUMÁRIO DOS DADOS ===")
            logger.info(f"Total de registros: {summary['total_registros']}")
            logger.info(f"Médicos únicos: {summary['medicos_unicos']}")
            logger.info(f"Pacientes únicos: {summary['pacientes_unicos']}")
            logger.info(f"Período: {summary['data_minima']} a {summary['data_maxima']}")
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao gerar sumário: {str(e)}")
            return {}

    def get_by_doctor(self, doctor_name):
        """
        Obter dados filtrados por médico
        
        Args:
            doctor_name: Nome do médico
            
        Returns:
            DataFrame filtrado
        """
        if 'medico' not in self.df.columns:
            logger.error("Coluna 'medico' não encontrada")
            return pd.DataFrame()
        
        filtered = self.df[self.df['medico'].str.contains(doctor_name, case=False, na=False)]
        logger.info(f"Filtrado para {doctor_name}: {len(filtered)} registros")
        
        return filtered

    def export_to_excel(self, output_file, by_doctor=False):
        """
        Exportar dados para Excel
        
        Args:
            output_file: Caminho do arquivo de saída
            by_doctor: Se True, cria abas por médico
        """
        try:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                if by_doctor and 'medico' in self.df.columns:
                    # Criar uma aba para cada médico
                    doctors = self.df['medico'].unique()
                    for doctor in doctors:
                        doctor_data = self.get_by_doctor(doctor)
                        sheet_name = str(doctor)[:31]  # Excel limita nome da aba a 31 caracteres
                        doctor_data.to_excel(writer, sheet_name=sheet_name, index=False)
                        logger.info(f"Aba '{sheet_name}' criada")
                else:
                    # Exportar tudo em uma aba
                    self.df.to_excel(writer, sheet_name='Dados', index=False)
                    logger.info("Aba 'Dados' criada")
            
            logger.info(f"Arquivo exportado: {output_file}")
            
        except Exception as e:
            logger.error(f"Erro ao exportar para Excel: {str(e)}")
            raise

    def run(self, csv_file, output_excel):
        """
        Executar processamento completo
        
        Args:
            csv_file: Arquivo CSV de entrada
            output_excel: Arquivo Excel de saída
        """
        try:
            self.load_data(csv_file)
            self.clean_data()
            self.validate_data()
            self.get_summary()
            self.export_to_excel(output_excel, by_doctor=True)
            
            logger.info("Processamento concluído com sucesso!")
            return self.df
            
        except Exception as e:
            logger.error(f"Erro durante processamento: {str(e)}")
            raise


# Exemplo de uso
if __name__ == "__main__":
    processor = DataProcessor()
    
    # Processar dados
    df = processor.run(
        csv_file="dados_clinicys.csv",
        output_excel="dados_processados.xlsx"
    )
    
    print("\nPrimeiras linhas dos dados processados:")
    print(df.head())
