package com.fintrack.crm;

public class Cliente {
    private String nome;
    private String telefone;
    private String veiculo;
    private String placa;

    public Cliente() {}

    public Cliente(String nome, String telefone, String veiculo, String placa) {
        this.nome = nome;
        this.telefone = telefone;
        this.veiculo = veiculo != null ? veiculo : "";
        this.placa = placa != null ? placa : "";
    }

    public String getNome() { return nome; }
    public void setNome(String nome) { this.nome = nome; }
    public String getTelefone() { return telefone; }
    public void setTelefone(String telefone) { this.telefone = telefone; }
    public String getVeiculo() { return veiculo != null ? veiculo : ""; }
    public void setVeiculo(String veiculo) { this.veiculo = veiculo; }
    public String getPlaca() { return placa != null ? placa : ""; }
    public void setPlaca(String placa) { this.placa = placa; }
}
