-- CreateTable
CREATE TABLE "Professor" (
    "Professor_ID" SERIAL NOT NULL,
    "Nome" VARCHAR(255) NOT NULL,
    "Email" VARCHAR(255) NOT NULL,
    "Senha" VARCHAR(255) NOT NULL,

    CONSTRAINT "Professor_pkey" PRIMARY KEY ("Professor_ID")
);

-- CreateTable
CREATE TABLE "Impressora" (
    "Impressora_ID" SERIAL NOT NULL,
    "IP" VARCHAR(100) NOT NULL,
    "Nome" VARCHAR(150) NOT NULL,
    "ID_Professor" INTEGER NOT NULL,

    CONSTRAINT "Impressora_pkey" PRIMARY KEY ("Impressora_ID")
);

-- CreateTable
CREATE TABLE "Impressao3D" (
    "Impressao3D_ID" SERIAL NOT NULL,
    "DataInicio" TIMESTAMP(3) NOT NULL,
    "DataConclusao" TIMESTAMP(3) NOT NULL,
    "ID_Arquivo3D" INTEGER NOT NULL,
    "ID_Impressora" INTEGER NOT NULL,

    CONSTRAINT "Impressao3D_pkey" PRIMARY KEY ("Impressao3D_ID")
);

-- CreateTable
CREATE TABLE "Arquivo3D" (
    "Arquivo3D_ID" SERIAL NOT NULL,
    "Versao" INTEGER NOT NULL,
    "URL" VARCHAR(255) NOT NULL,
    "ID_DICOM" INTEGER NOT NULL,

    CONSTRAINT "Arquivo3D_pkey" PRIMARY KEY ("Arquivo3D_ID")
);

-- CreateTable
CREATE TABLE "DICOM" (
    "DICOM_ID" SERIAL NOT NULL,
    "Nome" VARCHAR(100),
    "Paciente" VARCHAR(255),
    "URL" VARCHAR(255) NOT NULL,
    "ID_Professor" INTEGER NOT NULL,

    CONSTRAINT "DICOM_pkey" PRIMARY KEY ("DICOM_ID")
);

-- CreateIndex
CREATE UNIQUE INDEX "Professor_Email_key" ON "Professor"("Email");

-- AddForeignKey
ALTER TABLE "Impressora" ADD CONSTRAINT "Impressora_ID_Professor_fkey" FOREIGN KEY ("ID_Professor") REFERENCES "Professor"("Professor_ID") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Impressao3D" ADD CONSTRAINT "Impressao3D_ID_Arquivo3D_fkey" FOREIGN KEY ("ID_Arquivo3D") REFERENCES "Arquivo3D"("Arquivo3D_ID") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Impressao3D" ADD CONSTRAINT "Impressao3D_ID_Impressora_fkey" FOREIGN KEY ("ID_Impressora") REFERENCES "Impressora"("Impressora_ID") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Arquivo3D" ADD CONSTRAINT "Arquivo3D_ID_DICOM_fkey" FOREIGN KEY ("ID_DICOM") REFERENCES "DICOM"("DICOM_ID") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DICOM" ADD CONSTRAINT "DICOM_ID_Professor_fkey" FOREIGN KEY ("ID_Professor") REFERENCES "Professor"("Professor_ID") ON DELETE RESTRICT ON UPDATE CASCADE;
