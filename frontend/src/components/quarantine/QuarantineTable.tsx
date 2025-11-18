import { useState } from "react";
import { AlertTriangle } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
  PaginationEllipsis,
} from "@/components/ui/pagination";
import { useQuarantine } from "./hooks/useQuarantine";
import { useQuarantineActions } from "./hooks/useQuarantineActions";
import { QuarantineHeader } from "./QuarantineHeader";
import { QuarantineTableRow } from "./QuarantineTableRow";
import type { QuarantineTableProps } from "./types";

export const QuarantineTable = ({ limit, showHeader = true }: QuarantineTableProps) => {
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = limit || 20;
  
  const { emails, pagination, loading, error, reload, loadPage } = useQuarantine(currentPage, pageSize, limit);
  const { handleRelease, handleDelete } = useQuarantineActions(reload);

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
    loadPage(newPage);
    // Scroll to top of table
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const renderPagination = () => {
    if (!pagination || pagination.total_pages <= 1) {
      return null;
    }

    const pages: (number | string)[] = [];
    const totalPages = pagination.total_pages;
    const current = pagination.page;

    // Always show first page
    if (totalPages > 0) {
      pages.push(1);
    }

    // Calculate page range to show
    let startPage = Math.max(2, current - 1);
    let endPage = Math.min(totalPages - 1, current + 1);

    // Adjust if we're near the start
    if (current <= 3) {
      endPage = Math.min(5, totalPages - 1);
    }

    // Adjust if we're near the end
    if (current >= totalPages - 2) {
      startPage = Math.max(2, totalPages - 4);
    }

    // Add ellipsis after first page if needed
    if (startPage > 2) {
      pages.push('ellipsis-start');
    }

    // Add pages in range
    for (let i = startPage; i <= endPage; i++) {
      if (i > 1 && i < totalPages) {
        pages.push(i);
      }
    }

    // Add ellipsis before last page if needed
    if (endPage < totalPages - 1) {
      pages.push('ellipsis-end');
    }

    // Always show last page
    if (totalPages > 1) {
      pages.push(totalPages);
    }

    return (
      <Pagination className="mt-6">
        <PaginationContent>
          <PaginationItem>
            <PaginationPrevious
              href="#"
              onClick={(e) => {
                e.preventDefault();
                if (pagination.has_previous) {
                  handlePageChange(current - 1);
                }
              }}
              className={!pagination.has_previous ? "pointer-events-none opacity-50" : "cursor-pointer"}
            />
          </PaginationItem>
          
          {pages.map((page, index) => {
            if (page === 'ellipsis-start' || page === 'ellipsis-end') {
              return (
                <PaginationItem key={`ellipsis-${index}`}>
                  <PaginationEllipsis />
                </PaginationItem>
              );
            }
            
            const pageNum = page as number;
            return (
              <PaginationItem key={pageNum}>
                <PaginationLink
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    handlePageChange(pageNum);
                  }}
                  isActive={pageNum === current}
                  className="cursor-pointer"
                >
                  {pageNum}
                </PaginationLink>
              </PaginationItem>
            );
          })}
          
          <PaginationItem>
            <PaginationNext
              href="#"
              onClick={(e) => {
                e.preventDefault();
                if (pagination.has_next) {
                  handlePageChange(current + 1);
                }
              }}
              className={!pagination.has_next ? "pointer-events-none opacity-50" : "cursor-pointer"}
            />
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    );
  };

  if (loading) {
    return (
      <div className="bg-card rounded-xl border border-border overflow-hidden animate-slide-up">
        {showHeader && (
          <div className="p-6 border-b border-border">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              <h2 className="text-lg font-semibold">Quarantined Emails</h2>
            </div>
          </div>
        )}
        <div className="p-8 text-center text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-card rounded-xl border border-border overflow-hidden animate-slide-up">
        {showHeader && (
          <div className="p-6 border-b border-border">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              <h2 className="text-lg font-semibold">Quarantined Emails</h2>
            </div>
          </div>
        )}
        <div className="p-8 text-center text-destructive">{error}</div>
      </div>
    );
  }

  return (
    <div className="bg-card rounded-xl border border-border overflow-hidden animate-slide-up">
      {showHeader && <QuarantineHeader onRefresh={reload} />}

      <div className="overflow-x-auto">
        {emails.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            No quarantined emails found
          </div>
        ) : (
          <>
            {pagination && (
              <div className="px-6 py-4 text-sm text-muted-foreground border-b border-border">
                Showing {((pagination.page - 1) * pagination.page_size) + 1} to{" "}
                {Math.min(pagination.page * pagination.page_size, pagination.total_count)} of{" "}
                {pagination.total_count} emails
              </div>
            )}
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Sender</TableHead>
                  <TableHead>Subject</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Threat</TableHead>
                  <TableHead>Score</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {emails.map((email) => (
                  <QuarantineTableRow
                    key={email.id}
                    email={email}
                    onRelease={handleRelease}
                    onDelete={handleDelete}
                  />
                ))}
              </TableBody>
            </Table>
            {renderPagination()}
          </>
        )}
      </div>
    </div>
  );
};

