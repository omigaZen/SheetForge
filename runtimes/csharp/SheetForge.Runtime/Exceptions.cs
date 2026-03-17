using System;

namespace SheetForge
{
    public class SheetForgeException : Exception
    {
        public string? TableName { get; }

        public SheetForgeException(string message) : base(message)
        {
        }

        public SheetForgeException(string tableName, string message) : base($"[{tableName}] {message}")
        {
            TableName = tableName;
        }
    }

    public class DataLoadException : SheetForgeException
    {
        public string FilePath { get; }

        public DataLoadException(string filePath, string message) : base($"Failed to load '{filePath}': {message}")
        {
            FilePath = filePath;
        }
    }

    public class InvalidDataFormatException : SheetForgeException
    {
        public InvalidDataFormatException(string message) : base(message)
        {
        }
    }
}
