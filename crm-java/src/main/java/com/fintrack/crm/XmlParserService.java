package com.fintrack.crm;

import org.springframework.stereotype.Service;
import org.w3c.dom.*;
import javax.xml.parsers.*;
import java.io.*;
import java.util.ArrayList;
import java.util.List;

@Service
public class XmlParserService {

    public List<Cliente> parsearXml(InputStream inputStream) throws Exception {
        List<Cliente> clientes = new ArrayList<>();

        // Remove BOM (UTF-8: EF BB BF) se presente
        PushbackInputStream pbStream = new PushbackInputStream(inputStream, 3);
        byte[] bom = new byte[3];
        int read = pbStream.read(bom, 0, 3);
        if (read == 3 && bom[0] == (byte) 0xEF && bom[1] == (byte) 0xBB && bom[2] == (byte) 0xBF) {
            // BOM detectado e descartado
        } else if (read > 0) {
            pbStream.unread(bom, 0, read);
        }

        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        DocumentBuilder builder = factory.newDocumentBuilder();
        Document doc = builder.parse(pbStream);
        doc.getDocumentElement().normalize();

        NodeList nodeList = doc.getElementsByTagName("cliente");

        for (int i = 0; i < nodeList.getLength(); i++) {
            Node node = nodeList.item(i);
            if (node.getNodeType() != Node.ELEMENT_NODE) continue;

            Element el = (Element) node;
            String nome = extrairTexto(el, "nome");
            String telefone = extrairTexto(el, "telefone");
            String veiculo = extrairTexto(el, "veiculo");
            String placa = extrairTexto(el, "placa");

            if (nome.isEmpty() || telefone.isEmpty()) continue;

            clientes.add(new Cliente(corrigirNome(nome), telefone, veiculo, placa));
        }

        return clientes;
    }

    private String extrairTexto(Element el, String tag) {
        NodeList list = el.getElementsByTagName(tag);
        if (list.getLength() == 0) return "";
        return list.item(0).getTextContent().trim();
    }

    public String corrigirNome(String nome) {
        if (nome == null || nome.isBlank()) return "";
        String corrigido = nome
            .replaceAll("[\\p{Cntrl}&&[^\r\n\t]]", "")
            .replaceAll("\\s+", " ")
            .trim();

        String[] palavras = corrigido.toLowerCase().split(" ");
        StringBuilder sb = new StringBuilder();
        String[] preposicoes = {"de", "da", "do", "das", "dos", "e", "a", "o"};
        for (int i = 0; i < palavras.length; i++) {
            String p = palavras[i];
            if (i > 0 && isPreposcao(p, preposicoes)) {
                sb.append(p);
            } else if (!p.isEmpty()) {
                sb.append(Character.toUpperCase(p.charAt(0))).append(p.substring(1));
            }
            if (i < palavras.length - 1) sb.append(" ");
        }
        return sb.toString();
    }

    private boolean isPreposcao(String palavra, String[] lista) {
        for (String p : lista) {
            if (p.equals(palavra)) return true;
        }
        return false;
    }
}
