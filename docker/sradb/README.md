```R
sqlfile <- '/db/SRAmetadb.sqlite'
sra_con <- dbConnect(SQLite(), sqlfile)

q <- function(x) {
    res <- dbGetQuery(sra_con, x)
    res[, !duplicated(colnames(res))]
}

q(paste(
'SELECT * FROM sra, study, submission, fastq, run',
'WHERE sra.submission_accession = submission.submission_accession',
'  AND sra.study_accession = study.study_accession',
'  AND sra.run_accession = fastq.run_accession',
'  AND sra.run_accession = run.run_accession',
'  AND fastq.FASTQ_FILES > 0',
sprintf('AND sra.study_accession = "%s"', proj)))
```

```bash
/* All the human RNA-seq, I think */
SELECT COUNT(*) FROM sra, experiment
  WHERE sra.experiment_accession = experiment.experiment_accession
    AND experiment.library_strategy = 'RNA-Seq'
    AND experiment.library_source = 'TRANSCRIPTOMIC'
    AND experiment.platform = 'ILLUMINA'
    AND sra.taxon_id = 9606

/* Ans: 200226 */


/* ===============  Create temporary table  ============== */

CREATE TEMPORARY TABLE HUMAN_RNA AS
WITH FT_CTE AS (
  SELECT *
  FROM sra,
       study,
       experiment,
       submission,
       fastq,
       run
  WHERE sra.submission_accession = submission.submission_accession
    AND sra.study_accession = study.study_accession
    AND sra.run_accession = fastq.run_accession
    AND sra.run_accession = run.run_accession
    AND sra.experiment_accession = experiment.experiment_accession
    AND fastq.FASTQ_FILES > 0
    AND experiment.library_strategy = 'RNA-Seq'
    AND experiment.library_source = 'TRANSCRIPTOMIC'
    AND experiment.platform = 'ILLUMINA'
    AND sra.taxon_id = 9606
  )
SELECT * FROM FT_CTE;

SELECT COUNT(*) FROM HUMAN_RNA

.databases

/* ======================================================= */


/* Now trying to remove the dbGaP protected */
SELECT COUNT(*) FROM sra, experiment, fastq
  WHERE sra.run_accession = fastq.run_accession
    AND sra.experiment_accession = experiment.experiment_accession
    AND experiment.library_strategy = 'RNA-Seq'
    AND experiment.library_source = 'TRANSCRIPTOMIC'
    AND experiment.platform = 'ILLUMINA'
    AND sra.taxon_id = 9606
    AND fastq.FASTQ_FILES > 0

/* Ans: 168340 */

/* Now for some single-cell */
SELECT COUNT(*) FROM sra, experiment, study
  WHERE sra.experiment_accession = experiment.experiment_accession
    AND study.study_accession = sra.study_accession
    AND experiment.library_strategy = 'RNA-Seq'
    AND experiment.library_source = 'TRANSCRIPTOMIC'
    AND experiment.platform = 'ILLUMINA'
    AND (   study.study_abstract LIKE '%single-cell%'
         OR study.study_title LIKE '%single-cell%'
         OR experiment.library_construction_protocol LIKE '%single-cell%')
    AND sra.taxon_id = 9606

/* Ans: 55883 */

/* Now single-cell and non-dbGaP */
SELECT COUNT(*) FROM sra, experiment, study, fastq
  WHERE sra.run_accession = fastq.run_accession
    AND sra.experiment_accession = experiment.experiment_accession
    AND study.study_accession = sra.study_accession
    AND experiment.library_strategy = 'RNA-Seq'
    AND experiment.library_source = 'TRANSCRIPTOMIC'
    AND experiment.platform = 'ILLUMINA'
    AND (   study.study_abstract LIKE '%single-cell%'
         OR study.study_title LIKE '%single-cell%'
         OR experiment.library_construction_protocol LIKE '%single-cell%')
    AND sra.taxon_id = 9606
    AND fastq.FASTQ_FILES > 0

/* Ans: 51403 */

/* Is this a good way to get 1/10th of the human data? */
SELECT COUNT(*) FROM sra, experiment
  WHERE sra.experiment_accession = experiment.experiment_accession
    AND experiment.library_strategy = 'RNA-Seq'
    AND experiment.library_source = 'TRANSCRIPTOMIC'
    AND experiment.platform = 'ILLUMINA'
    AND sra.taxon_id = 9606
    AND sra.study_accession LIKE '%0'

/* 19578 */

SELECT COUNT(*) FROM sra, experiment
  WHERE sra.experiment_accession = experiment.experiment_accession
    AND experiment.library_strategy = 'RNA-Seq'
    AND experiment.library_source = 'TRANSCRIPTOMIC'
    AND experiment.platform = 'ILLUMINA'
    AND sra.taxon_id = 9606
    AND sra.study_accession LIKE '%1'

/* 17737 */

SELECT COUNT(*) FROM sra, experiment
  WHERE sra.experiment_accession = experiment.experiment_accession
    AND experiment.library_strategy = 'RNA-Seq'
    AND experiment.library_source = 'TRANSCRIPTOMIC'
    AND experiment.platform = 'ILLUMINA'
    AND sra.taxon_id = 9606
    AND sra.study_accession LIKE '%2'

/* 29973 */

SELECT COUNT(*) FROM sra, experiment
  WHERE sra.experiment_accession = experiment.experiment_accession
    AND experiment.library_strategy = 'RNA-Seq'
    AND experiment.library_source = 'TRANSCRIPTOMIC'
    AND experiment.platform = 'ILLUMINA'
    AND sra.taxon_id = 9606
    AND sra.study_accession LIKE '%3'

/* 13735 */

SELECT COUNT(*) FROM sra, experiment
  WHERE sra.experiment_accession = experiment.experiment_accession
    AND experiment.library_strategy = 'RNA-Seq'
    AND experiment.library_source = 'TRANSCRIPTOMIC'
    AND experiment.platform = 'ILLUMINA'
    AND sra.taxon_id = 9606
    AND sra.study_accession LIKE '%4'

/* 17165 */

SELECT COUNT(*) FROM sra, experiment
  WHERE sra.experiment_accession = experiment.experiment_accession
    AND experiment.library_strategy = 'RNA-Seq'
    AND experiment.library_source = 'TRANSCRIPTOMIC'
    AND experiment.platform = 'ILLUMINA'
    AND sra.taxon_id = 9606
    AND sra.study_accession LIKE '%5'

/* 17165 */

SELECT COUNT(*) FROM sra, study, experiment, submission, fastq, run
  WHERE sra.submission_accession = submission.submission_accession
    AND sra.study_accession = study.study_accession
    AND sra.run_accession = fastq.run_accession
    AND sra.run_accession = run.run_accession
    AND sra.experiment_accession = experiment.experiment_accession
    AND fastq.FASTQ_FILES > 0
    AND experiment.library_strategy = 'RNA-Seq'
    AND experiment.library_source = 'TRANSCRIPTOMIC'
    AND experiment.platform = 'ILLUMINA'
    AND sra.taxon_id = 9606
LIMIT 100

```