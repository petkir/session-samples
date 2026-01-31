using System.Text;
using iText.Kernel.Pdf;
using iText.Kernel.Pdf.Canvas.Parser;
using iText.Kernel.Pdf.Canvas.Parser.Listener;

namespace Indexer.Services;

public static class PdfReader
{
    public static string ExtractText(string pdfPath)
    {
        var text = new StringBuilder();

        using var pdfReader = new iText.Kernel.Pdf.PdfReader(pdfPath);
        using var pdfDocument = new PdfDocument(pdfReader);

        for (int page = 1; page <= pdfDocument.GetNumberOfPages(); page++)
        {
            var strategy = new LocationTextExtractionStrategy();
            var pageText = PdfTextExtractor.GetTextFromPage(pdfDocument.GetPage(page), strategy);
            
            if (!string.IsNullOrWhiteSpace(pageText))
            {
                text.AppendLine(pageText);
                text.AppendLine(); // Add spacing between pages
            }
        }

        return text.ToString();
    }
}
