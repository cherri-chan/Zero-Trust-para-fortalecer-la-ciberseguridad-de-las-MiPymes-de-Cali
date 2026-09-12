# Arquitectura Zero Trust

A continuación se presenta el diagrama de arquitectura:

```mermaid
flowchart TD
    subgraph Entidades [1. Puntos de Entrada]
        U[Usuario empresarial]
        A[Administrador]
        D[Dispositivo autorizado]
        R[Dispositivo no autorizado]
    end

    subgraph Perimetro [2. Perímetro de Red]
        FW[Firewall / Router]
        VPN[VPN de acceso remoto]
    end

    subgraph Segmentos [3. Segmentos de Red]
        SEG1[Segmento de usuarios]
        SEG2[Segmento de administración]
        SEG3[Segmento de recursos protegidos]
    end

    subgraph ZeroTrust [4. Núcleo Zero Trust]
        IDP[Proveedor de identidad]
        MFA[Servicio MFA]
        INV[Inventario de dispositivos]
        PDP[Motor de políticas]
        PEP[Controlador de acceso]
        APP[Aplicación administrativa]
    end

    subgraph Auditoria [5. Datos y Monitoreo]
        DB[(Base de datos)]
        SIEM[Registro y monitoreo]
        BACKUP[Respaldo]
    end

    subgraph Recursos [6. Recursos Protegidos]
        RES1[Aplicación empresarial]
        RES2[Servidor de archivos]
        RES3[Base de datos protegida]
    end

    U --> D
    A --> D
    R --> FW
    D --> FW

    FW --> VPN
    FW --> SEG1
    FW --> SEG2

    SEG1 --> IDP
    SEG2 --> APP

    IDP --> MFA
    IDP --> PDP
    INV --> PDP
    PDP --> PEP

    R -.->|Solicitud evaluada| PDP
    PDP -.->|Denegar si no cumple| R

    PEP --> SEG3
    SEG3 --> RES1
    SEG3 --> RES2
    SEG3 --> RES3

    APP --> DB
    PDP --> DB
    PEP --> SIEM
    IDP --> SIEM
    FW --> SIEM

    SIEM --> BACKUP
    DB --> BACKUP
    
    classDef redBox fill:#ffebee,stroke:#c62828,stroke-width:2px;
    class R redBox;
