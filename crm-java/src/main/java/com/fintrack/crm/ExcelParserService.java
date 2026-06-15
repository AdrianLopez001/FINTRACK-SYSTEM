package com.fintrack.crm;

import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.io.InputStream;
import java.util.*;

@Service
public class ExcelParserService {

    @Autowired
    private XmlParserService xmlParserService;

    public List<Cliente> parsearExcel(InputStream inputStream) throws Exception {
        List<Cliente> clientes = new ArrayList<>();

        Workbook wb = new XSSFWorkbook(inputStream);
        Sheet sheet = wb.getSheetAt(0);

        // Descobre o índice de cada coluna pelo cabeçalho (linha 0)
        Row header = sheet.getRow(0);
        if (header == null) { wb.close(); return clientes; }

        Map<String, Integer> colunas = new HashMap<>();
        for (Cell cell : header) {
            String titulo = cell.getStringCellValue().trim();
            colunas.put(titulo, cell.getColumnIndex());
        }

        // Mapeia nomes de coluna do relatório CRM BI da Cartec
        int colNome     = colIdx(colunas, "Nome");
        int colTel1     = colIdx(colunas, "Primeiro Telefone");
        int colTelSms   = colIdx(colunas, "Telefone SMS");
        int colVeiculo  = colIdx(colunas, "Última Venda - Veículo", "Ultima Venda - Veiculo");
        int colPlaca    = colIdx(colunas, "Última Venda - Placa", "Ultima Venda - Placa");

        for (int r = 1; r <= sheet.getLastRowNum(); r++) {
            Row row = sheet.getRow(r);
            if (row == null) continue;

            String nome    = texto(row, colNome);
            // Prefere Telefone SMS, fallback Primeiro Telefone
            String tel     = colTelSms >= 0 ? texto(row, colTelSms) : "";
            if (tel.isBlank() && colTel1 >= 0) tel = texto(row, colTel1);
            String veiculo = colVeiculo >= 0 ? texto(row, colVeiculo) : "";
            String placa   = colPlaca  >= 0 ? texto(row, colPlaca)   : "";

            if (nome.isBlank() || tel.isBlank()) continue;

            clientes.add(new Cliente(xmlParserService.corrigirNome(nome), tel, veiculo, placa));
        }

        wb.close();
        return clientes;
    }

    // Busca coluna por um ou mais nomes alternativos (case-insensitive)
    private int colIdx(Map<String, Integer> colunas, String... nomes) {
        for (String nome : nomes) {
            for (Map.Entry<String, Integer> e : colunas.entrySet()) {
                if (e.getKey().equalsIgnoreCase(nome) || normalize(e.getKey()).equalsIgnoreCase(normalize(nome))) {
                    return e.getValue();
                }
            }
        }
        return -1;
    }

    private String normalize(String s) {
        return s == null ? "" : s
            .replace("ú", "u").replace("Ú", "U")
            .replace("é", "e").replace("É", "E")
            .replace("ã", "a").replace("Ã", "A")
            .replace("ç", "c").replace("Ç", "C")
            .replace("í", "i").replace("Í", "I");
    }

    private String texto(Row row, int idx) {
        if (idx < 0) return "";
        Cell cell = row.getCell(idx, Row.MissingCellPolicy.RETURN_BLANK_AS_NULL);
        if (cell == null) return "";
        return switch (cell.getCellType()) {
            case STRING  -> cell.getStringCellValue().trim();
            case NUMERIC -> {
                double v = cell.getNumericCellValue();
                yield String.valueOf((long) v);
            }
            default -> "";
        };
    }
}
