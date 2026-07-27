import { useEffect, useState } from "react";
import { Modal, Spinner, Button } from "../ui";
import { useViewActiveResumePdf } from "../../hooks/useResume";
import { AlertCircle, Download, FileText } from "lucide-react";

interface ResumeViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  filename?: string;
}

export default function ResumeViewerModal({ isOpen, onClose, filename = "Active Resume" }: ResumeViewerModalProps) {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  const viewPdfMutation = useViewActiveResumePdf();

  useEffect(() => {
    if (isOpen) {
      setErrorMessage(null);
      viewPdfMutation.mutate(undefined, {
        onSuccess: (blob) => {
          const url = URL.createObjectURL(blob);
          setPdfUrl(url);
        },
        onError: (error: any) => {
          let message = "Failed to load resume PDF. Please try again.";
          
          if (error.response) {
            const status = error.response.status;
            if (status === 401 || status === 403) {
              message = "Your session has expired or you do not have permission. Please log in again.";
            } else if (status === 404) {
              message = "No active resume was found. Please ensure you have uploaded and activated a resume.";
            }
          }
          
          setErrorMessage(message);
        }
      });
    }

    return () => {
      // Cleanup Object URL when modal closes or unmounts
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl);
        setPdfUrl(null);
      }
    };
    // We intentionally don't put pdfUrl in deps to avoid revoking immediately after creation
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  // Handle explicit modal close (also runs cleanup because isOpen changes)
  const handleClose = () => {
    if (pdfUrl) {
      URL.revokeObjectURL(pdfUrl);
      setPdfUrl(null);
    }
    viewPdfMutation.reset();
    setErrorMessage(null);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={`Viewing: ${filename}`}
      size="xl"
    >
      <div className="flex flex-col h-[70vh] sm:h-[80vh] w-full">
        {viewPdfMutation.isPending && (
          <div className="flex flex-col items-center justify-center flex-1 space-y-4">
            <Spinner size="lg" />
            <p className="text-sm text-text-secondary animate-pulse">
              Securely fetching your resume...
            </p>
          </div>
        )}

        {errorMessage && (
          <div className="flex flex-col items-center justify-center flex-1 space-y-4 p-6 text-center">
            <div className="h-16 w-16 rounded-full bg-error/10 flex items-center justify-center text-error">
              <AlertCircle size={32} />
            </div>
            <div className="space-y-1">
              <h3 className="text-lg font-bold text-text">Unable to View Resume</h3>
              <p className="text-sm text-text-secondary max-w-md mx-auto">
                {errorMessage}
              </p>
            </div>
            <Button variant="secondary" onClick={handleClose} className="mt-4">
              Close Viewer
            </Button>
          </div>
        )}

        {!viewPdfMutation.isPending && !errorMessage && pdfUrl && (
          <div className="flex-1 w-full bg-surface-elevated rounded-lg overflow-hidden flex flex-col relative border border-border">
            {/* Fallback download if <object> fails or browser blocks it */}
            <object
              data={pdfUrl}
              type="application/pdf"
              className="w-full h-full"
              title="Resume PDF Viewer"
            >
              <div className="flex flex-col items-center justify-center h-full space-y-4 p-8 text-center bg-surface">
                <FileText size={48} className="text-primary/50" />
                <div className="space-y-1">
                  <h3 className="text-lg font-semibold">Browser Cannot Display PDF</h3>
                  <p className="text-sm text-text-secondary max-w-sm mx-auto">
                    Your browser does not support inline PDF viewing. You can download the file instead.
                  </p>
                </div>
                <a
                  href={pdfUrl}
                  download={filename || "resume.pdf"}
                  className="mt-2 inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground text-sm font-medium rounded-lg hover:bg-primary/90 transition-colors"
                >
                  <Download size={16} />
                  Download PDF
                </a>
              </div>
            </object>
          </div>
        )}
      </div>
    </Modal>
  );
}
