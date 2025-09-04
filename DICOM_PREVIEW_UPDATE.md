# Atualização: Preview de Imagem DICOM

## Resumo das Mudanças

Esta atualização adiciona a funcionalidade de extração e armazenamento de imagens de preview para arquivos DICOM. Quando um arquivo DICOM é enviado, o sistema agora:

1. Extrai automaticamente uma imagem de preview do primeiro arquivo DICOM
2. Faz upload da imagem para o S3 em formato PNG
3. Armazena a URL da imagem no banco de dados
4. Retorna a URL junto com os outros dados da entidade

## Arquivos Modificados

### 1. Schema do Banco de Dados (`prisma/schema.prisma`)
- Adicionada coluna `dicom_image_preview` ao modelo `DICOM`

### 2. Schemas Pydantic (`app/dicom/schemas.py`)
- Adicionado campo `dicom_image_preview` ao schema `DICOMResponse`

### 3. Service DICOM (`app/dicom/service.py`)
- Importação do processador de DICOM
- Modificação do método `create_dicom_upload` para extrair preview
- Atualização do método `_map_to_response` para incluir o novo campo
- Limpeza automática da imagem de preview em caso de erro

### 4. Novo Processador DICOM (`app/utils/dicom_processor.py`)
- Função `extract_dicom_preview()` para extrair imagem do DICOM
- Função `normalize_pixel_array()` para normalizar valores de pixel
- Função `get_dicom_metadata()` para extrair metadados do DICOM

### 5. Migração do Banco (`prisma/migrations/20250103120000_add_dicom_image_preview/migration.sql`)
- SQL para adicionar a nova coluna ao banco de dados

## Funcionalidades Implementadas

### Extração de Preview
- Suporte a arquivos DICOM 2D e 3D
- Para arquivos 3D, extrai o slice do meio
- Normalização automática de valores de pixel
- Redimensionamento para 512x512 pixels (mantendo proporção)
- Conversão para formato PNG

### Upload para S3
- Armazenamento em pasta separada (`dicom-previews/`)
- Nomenclatura única com UUID
- Content-Type correto (`image/png`)
- Limpeza automática em caso de erro

### Tratamento de Erros
- Continua o processo mesmo se falhar a extração do preview
- Logs de erro para debugging
- Rollback automático em caso de falha no upload

## Como Usar

### Upload de Arquivo DICOM
O endpoint de upload continua funcionando da mesma forma, mas agora retorna também a URL da imagem de preview:

```json
{
  "id": 1,
  "nome": "Exame CT",
  "paciente": "João Silva",
  "professor_id": 1,
  "s3_urls": ["dicom-files/1/uuid1.dcm", "dicom-files/1/uuid2.dcm"],
  "dicom_image_preview": "dicom-previews/1/uuid3.png",
  "created_at": "2024-01-03T12:00:00Z",
  "updated_at": "2024-01-03T12:00:00Z"
}
```

### Acesso à Imagem de Preview
A URL da imagem de preview pode ser usada para:
- Exibir thumbnails na interface
- Pré-visualização rápida do conteúdo
- Geração de relatórios com imagens

## Dependências Adicionais

As seguintes bibliotecas são necessárias (já incluídas no `requirements.txt`):
- `pydicom>=2.4.4` - Processamento de arquivos DICOM
- `numpy>=1.26.0` - Manipulação de arrays
- `Pillow>=10.0.0` - Processamento de imagens
- `scikit-image>=0.21.0` - Processamento de imagem científica

## Migração do Banco de Dados

Para aplicar as mudanças no banco de dados:

1. Execute a migração:
```bash
prisma migrate dev --name add_dicom_image_preview
```

2. Ou execute manualmente:
```sql
ALTER TABLE "dicom" ADD COLUMN "dicom_image_preview" TEXT;
```

## Testes

Execute o script de teste para verificar a funcionalidade:
```bash
python test_dicom_preview.py
```

## Notas Importantes

1. **Performance**: A extração de preview é feita apenas do primeiro arquivo DICOM para otimizar performance
2. **Compatibilidade**: Funciona com arquivos DICOM 2D e 3D
3. **Fallback**: Se a extração falhar, o upload continua normalmente
4. **Storage**: As imagens de preview são armazenadas separadamente dos arquivos originais
5. **Limpeza**: Em caso de erro, tanto os arquivos quanto as imagens de preview são removidos do S3
