-- Per-page reading session: time spent on a page from open to "mark read".
-- Populated by lute.read.service.Service.mark_page_read.

CREATE TABLE IF NOT EXISTS "readingsessions" (
    "RsID" INTEGER NOT NULL,
    "RsTxID" INTEGER NULL,
    "RsLgID" INTEGER NOT NULL,
    "RsStartDate" DATETIME NULL,
    "RsEndDate" DATETIME NOT NULL,
    "RsWordCount" INTEGER NOT NULL,
    "RsDurationSec" INTEGER NULL,
    PRIMARY KEY ("RsID"),
    FOREIGN KEY ("RsTxID") REFERENCES "texts" ("TxID") ON DELETE SET NULL,
    FOREIGN KEY ("RsLgID") REFERENCES "languages" ("LgID") ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_rs_lg_date ON readingsessions(RsLgID, RsEndDate);
