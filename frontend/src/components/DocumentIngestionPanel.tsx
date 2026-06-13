import React from 'react';
import { Upload, Loader2, Sparkles, FileText } from 'lucide-react';
import type { IngestDraft } from '../utils/api';

interface DocumentIngestionPanelProps {
  selectedFile: File | null;
  setSelectedFile: (file: File | null) => void;
  isParsingDoc: boolean;
  parsedDraft: IngestDraft | null;
  setParsedDraft: React.Dispatch<React.SetStateAction<IngestDraft | null>>;
  ingestMetadata: any;
  isConfirmingIngest: boolean;
  uploadProgress: number;
  ingestSuccessMessage: string;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onUploadAndParse: () => void;
  onConfirmAndPersist: () => void;
}

export const DocumentIngestionPanel: React.FC<DocumentIngestionPanelProps> = ({
  selectedFile,
  isParsingDoc,
  parsedDraft,
  setParsedDraft,
  ingestMetadata,
  isConfirmingIngest,
  uploadProgress,
  ingestSuccessMessage,
  onFileChange,
  onUploadAndParse,
  onConfirmAndPersist
}) => {
  return (
    <div className="flex flex-col gap-5 h-full">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="text-left">
          <h2 className="text-lg font-bold text-slate-200">Multimodal Document Ingestion Panel</h2>
          <p className="text-xs text-slate-500">Ingest handwritten case files, crime reports or notes. Parses OCR entities using Gemini with a human review validation layer.</p>
        </div>
      </div>

      {ingestSuccessMessage && (
        <div className="p-4 rounded-xl border border-emerald-950 bg-emerald-950/20 text-emerald-400 text-xs font-semibold animate-pulse text-left">
          🎉 {ingestSuccessMessage}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-grow">
        {/* Left side: Upload area */}
        <div className="glass-panel p-5 rounded-lg border border-slate-800 bg-slate-950/20 flex flex-col justify-between gap-6">
          <div className="flex flex-col gap-4">
            <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider text-left">
              Upload Case Document
            </h3>
            <div className="border-2 border-dashed border-slate-800 rounded-xl p-8 flex flex-col items-center justify-center gap-3 text-center bg-slate-950/40">
              <Upload className="w-10 h-10 text-slate-600 animate-bounce" />
              <div>
                <p className="text-xs text-slate-300 font-semibold">Select document image or handwritten note</p>
                <p className="text-[10px] text-slate-500 mt-1">PNG, JPG, PDF up to 10MB</p>
              </div>
              <input
                type="file"
                id="document-upload-input"
                onChange={onFileChange}
                className="hidden"
                accept="image/*,application/pdf"
              />
              <label
                htmlFor="document-upload-input"
                className="mt-2 px-3 py-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-xs text-cyan-400 font-bold rounded-lg cursor-pointer transition-colors"
              >
                Browse File
              </label>
            </div>

            {selectedFile && (
              <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800 flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-300 truncate max-w-[250px]">{selectedFile.name}</span>
                <span className="text-[10px] text-slate-500 font-mono">{(selectedFile.size / 1024).toFixed(1)} KB</span>
              </div>
            )}
          </div>

          {selectedFile && (
            <button
              onClick={onUploadAndParse}
              disabled={isParsingDoc}
              className="w-full py-2.5 bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold rounded-lg cursor-pointer transition-all shadow-md flex items-center justify-center gap-2"
            >
              {isParsingDoc ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Extracting Entities ({uploadProgress}%)</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Extract & Parse Document</span>
                </>
              )}
            </button>
          )}
        </div>

        {/* Right side: Human Review Form (Validation Layer) */}
        <div className="glass-panel p-5 rounded-lg border border-slate-800 bg-slate-950/20 flex flex-col justify-between">
          <div className="flex flex-col gap-4 overflow-y-auto max-h-[500px] pr-2">
            <div className="flex justify-between items-center border-b border-slate-900 pb-2">
              <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider text-left">
                Human Validation Layer
              </h3>
              <span className="text-[10px] text-slate-500 uppercase tracking-widest font-mono">
                Verification Required
              </span>
            </div>

            {ingestMetadata && (
              <div className="bg-slate-900/60 border border-slate-800 p-2.5 rounded-lg text-[10px] text-slate-400 text-left font-mono flex flex-wrap gap-x-4 gap-y-1">
                <div><span className="text-slate-500 font-bold">FILE:</span> {ingestMetadata.filename}</div>
                {ingestMetadata.operator && <div><span className="text-slate-500 font-bold">OPERATOR:</span> {ingestMetadata.operator}</div>}
                {ingestMetadata.timestamp && <div><span className="text-slate-500 font-bold">EXTRACTED:</span> {ingestMetadata.timestamp}</div>}
              </div>
            )}

            {!parsedDraft ? (
              <div className="text-center p-12 text-slate-600 text-xs uppercase tracking-widest flex flex-col items-center justify-center gap-3">
                <FileText className="w-12 h-12 text-slate-800" />
                Awaiting extraction. Upload a document to start reviews.
              </div>
            ) : (
              <div className="flex flex-col gap-4 text-xs">
                {/* FIR Details Section */}
                <div className="flex flex-col gap-2">
                  <h4 className="font-bold text-cyan-400 uppercase tracking-wider text-[10px] text-left">1. Incident Information</h4>
                  <div className="grid grid-cols-2 gap-3 bg-slate-950/40 p-3 rounded-lg border border-slate-900">
                    <div className="flex flex-col gap-1 text-left">
                      <label className="text-[9px] text-slate-500 font-bold uppercase tracking-wider">FIR Number</label>
                      <div className="flex gap-2 items-center">
                        <input
                          type="text"
                          value={parsedDraft.fir.fir_number.value}
                          onChange={(e) => setParsedDraft({
                            ...parsedDraft,
                            fir: { ...parsedDraft.fir, fir_number: { ...parsedDraft.fir.fir_number, value: e.target.value } }
                          })}
                          className="flex-1 bg-slate-900 border border-slate-800 text-slate-100 rounded p-1"
                        />
                        <span className={`text-[9px] font-bold px-1 rounded ${parsedDraft.fir.fir_number.confidence > 0.8 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                          {(parsedDraft.fir.fir_number.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    <div className="flex flex-col gap-1 text-left">
                      <label className="text-[9px] text-slate-500 font-bold uppercase tracking-wider">Date</label>
                      <div className="flex gap-2 items-center">
                        <input
                          type="text"
                          value={parsedDraft.fir.date.value}
                          onChange={(e) => setParsedDraft({
                            ...parsedDraft,
                            fir: { ...parsedDraft.fir, date: { ...parsedDraft.fir.date, value: e.target.value } }
                          })}
                          className="flex-1 bg-slate-900 border border-slate-800 text-slate-100 rounded p-1"
                        />
                        <span className={`text-[9px] font-bold px-1 rounded ${parsedDraft.fir.date.confidence > 0.8 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                          {(parsedDraft.fir.date.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    <div className="flex flex-col gap-1 text-left">
                      <label className="text-[9px] text-slate-500 font-bold uppercase tracking-wider">Crime Type</label>
                      <div className="flex gap-2 items-center">
                        <input
                          type="text"
                          value={parsedDraft.fir.crime_type.value}
                          onChange={(e) => setParsedDraft({
                            ...parsedDraft,
                            fir: { ...parsedDraft.fir, crime_type: { ...parsedDraft.fir.crime_type, value: e.target.value } }
                          })}
                          className="flex-1 bg-slate-900 border border-slate-800 text-slate-100 rounded p-1"
                        />
                        <span className={`text-[9px] font-bold px-1 rounded ${parsedDraft.fir.crime_type.confidence > 0.8 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                          {(parsedDraft.fir.crime_type.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    <div className="flex flex-col gap-1 text-left">
                      <label className="text-[9px] text-slate-500 font-bold uppercase tracking-wider">Location Name</label>
                      <div className="flex gap-2 items-center">
                        <input
                          type="text"
                          value={parsedDraft.fir.location_name.value}
                          onChange={(e) => setParsedDraft({
                            ...parsedDraft,
                            fir: { ...parsedDraft.fir, location_name: { ...parsedDraft.fir.location_name, value: e.target.value } }
                          })}
                          className="flex-1 bg-slate-900 border border-slate-800 text-slate-100 rounded p-1"
                        />
                        <span className={`text-[9px] font-bold px-1 rounded ${parsedDraft.fir.location_name.confidence > 0.8 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                          {(parsedDraft.fir.location_name.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    <div className="col-span-2 flex flex-col gap-1 text-left">
                      <label className="text-[9px] text-slate-500 font-bold uppercase tracking-wider">Description</label>
                      <textarea
                        value={parsedDraft.fir.description.value}
                        onChange={(e) => setParsedDraft({
                          ...parsedDraft,
                          fir: { ...parsedDraft.fir, description: { ...parsedDraft.fir.description, value: e.target.value } }
                        })}
                        className="w-full bg-slate-900 border border-slate-800 text-slate-100 rounded p-1.5 h-16"
                      />
                    </div>
                  </div>
                </div>

                {/* Accused Section */}
                <div className="flex flex-col gap-2 text-left">
                  <h4 className="font-bold text-cyan-400 uppercase tracking-wider text-[10px]">2. Extracted Suspects</h4>
                  {parsedDraft.accused.map((acc, idx) => (
                    <div key={idx} className="bg-slate-950/40 p-3 rounded-lg border border-slate-900 grid grid-cols-2 gap-2">
                      <div className="flex flex-col gap-1">
                        <label className="text-[9px] text-slate-500 font-bold uppercase tracking-wider">Name</label>
                        <input
                          type="text"
                          value={acc.name.value}
                          onChange={(e) => {
                            const updatedAcc = [...parsedDraft.accused];
                            updatedAcc[idx].name.value = e.target.value;
                            setParsedDraft({ ...parsedDraft, accused: updatedAcc });
                          }}
                          className="bg-slate-900 border border-slate-800 text-slate-100 rounded p-1"
                        />
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-[9px] text-slate-500 font-bold uppercase tracking-wider">Role</label>
                        <input
                          type="text"
                          value={acc.role.value}
                          onChange={(e) => {
                            const updatedAcc = [...parsedDraft.accused];
                            updatedAcc[idx].role.value = e.target.value;
                            setParsedDraft({ ...parsedDraft, accused: updatedAcc });
                          }}
                          className="bg-slate-900 border border-slate-800 text-slate-100 rounded p-1"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {parsedDraft && (
            <button
              onClick={onConfirmAndPersist}
              disabled={isConfirmingIngest}
              className="w-full py-2.5 mt-4 bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold rounded-lg cursor-pointer transition-all shadow-md flex items-center justify-center gap-2"
            >
              {isConfirmingIngest ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              <span>Confirm & Persist to Database</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
