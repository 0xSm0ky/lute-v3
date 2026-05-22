-- Log every change to a Term's status.
-- Populated by trigger trig_words_log_status_change
-- (see migrations_repeatable/trig_words.sql).

CREATE TABLE IF NOT EXISTS "wordstatuslog" (
    "WslID" INTEGER NOT NULL,
    "WslWoID" INTEGER NOT NULL,
    "WslLgID" INTEGER NOT NULL,
    "WslOldStatus" TINYINT NOT NULL,
    "WslNewStatus" TINYINT NOT NULL,
    "WslChangedDate" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("WslID"),
    FOREIGN KEY ("WslWoID") REFERENCES "words" ("WoID") ON DELETE CASCADE,
    FOREIGN KEY ("WslLgID") REFERENCES "languages" ("LgID") ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_wsl_date ON wordstatuslog(WslChangedDate);
CREATE INDEX IF NOT EXISTS idx_wsl_lg ON wordstatuslog(WslLgID);
