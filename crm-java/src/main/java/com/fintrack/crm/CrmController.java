package com.fintrack.crm;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

@Controller
@RequestMapping("/crm")
public class CrmController {

    @Autowired private XmlParserService xmlParserService;
    @Autowired private ExcelParserService excelParserService;

    @Value("${crm.mensagem.padrao}")
    private String mensagemPadrao;

    @GetMapping({"", "/"})
    public String index(Model model) {
        model.addAttribute("mensagemPadrao", mensagemPadrao.replace("\\n", "\n"));
        return "crm-index";
    }

    @PostMapping("/importar")
    public String importarArquivo(
            @RequestParam("arquivo") MultipartFile arquivo,
            @RequestParam("mensagemTemplate") String mensagemTemplate,
            Model model) {

        if (arquivo.isEmpty()) {
            model.addAttribute("erro", "Nenhum arquivo selecionado.");
            model.addAttribute("mensagemPadrao", mensagemTemplate);
            return "crm-index";
        }

        try {
            String nomeArquivo = arquivo.getOriginalFilename() != null
                ? arquivo.getOriginalFilename().toLowerCase() : "";

            List<Cliente> clientes;
            if (nomeArquivo.endsWith(".xlsx") || nomeArquivo.endsWith(".xls")) {
                clientes = excelParserService.parsearExcel(arquivo.getInputStream());
            } else {
                clientes = xmlParserService.parsearXml(arquivo.getInputStream());
            }

            if (clientes.isEmpty()) {
                model.addAttribute("erro", "Nenhum cliente encontrado. Verifique o formato do arquivo.");
                model.addAttribute("mensagemPadrao", mensagemTemplate);
                return "crm-index";
            }

            List<ClienteEnvio> envios = new ArrayList<>();
            for (Cliente c : clientes) {
                String numeroLimpo = c.getTelefone().replaceAll("\\D", "");
                if (numeroLimpo.length() == 11 || numeroLimpo.length() == 10) {
                    numeroLimpo = "55" + numeroLimpo;
                }

                String mensagemPersonalizada = mensagemTemplate
                    .replace("[nome]",    c.getNome())
                    .replace("[veiculo]", c.getVeiculo())
                    .replace("[placa]",   c.getPlaca())
                    .replace("\\n", "\n");

                String linkWhatsapp = "https://wa.me/" + numeroLimpo
                    + "?text=" + URLEncoder.encode(mensagemPersonalizada, StandardCharsets.UTF_8);

                envios.add(new ClienteEnvio(
                    c.getNome(), c.getTelefone(), numeroLimpo,
                    c.getVeiculo(), c.getPlaca(),
                    mensagemPersonalizada, linkWhatsapp
                ));
            }

            model.addAttribute("envios", envios);
            model.addAttribute("totalClientes", envios.size());
            return "crm-envio";

        } catch (Exception e) {
            model.addAttribute("erro", "Erro ao processar arquivo: " + e.getMessage());
            model.addAttribute("mensagemPadrao", mensagemTemplate);
            return "crm-index";
        }
    }

    public static class ClienteEnvio {
        public String nome;
        public String telefoneOriginal;
        public String telefoneFormatado;
        public String veiculo;
        public String placa;
        public String mensagem;
        public String linkWhatsapp;

        public ClienteEnvio(String nome, String telefoneOriginal, String telefoneFormatado,
                            String veiculo, String placa, String mensagem, String linkWhatsapp) {
            this.nome = nome;
            this.telefoneOriginal = telefoneOriginal;
            this.telefoneFormatado = telefoneFormatado;
            this.veiculo = veiculo;
            this.placa = placa;
            this.mensagem = mensagem;
            this.linkWhatsapp = linkWhatsapp;
        }
    }
}
