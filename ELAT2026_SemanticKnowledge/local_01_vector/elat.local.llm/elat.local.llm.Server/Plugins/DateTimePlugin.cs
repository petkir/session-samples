using System.ComponentModel;
using Microsoft.SemanticKernel;

namespace elat.local.llm.Server.Plugins;

public class DateTimePlugin
{
    [KernelFunction("getdate")]
    [Description("Returns the current date and time in UTC and local server time.")]
    public string GetDate()
    {
        var utcNow = DateTimeOffset.UtcNow;
        var localNow = DateTimeOffset.Now;

        return $"UTC: {utcNow:O}; Local: {localNow:O}";
    }
}
