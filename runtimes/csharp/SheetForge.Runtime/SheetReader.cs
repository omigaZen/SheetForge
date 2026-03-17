using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace SheetForge
{
    public sealed class SheetReader : IDisposable
    {
        private static readonly byte[] Magic = Encoding.ASCII.GetBytes("SFGC");

        private readonly BinaryReader _reader;
        private readonly Dictionary<int, string> _stringTable = new Dictionary<int, string>();
        private long _dataOffset;

        public SheetReader(string filePath)
        {
            _reader = new BinaryReader(File.OpenRead(filePath), Encoding.UTF8, false);
            ReadHeader();
            ReadColumnDefinitions();
            ReadStringTable();
            _reader.BaseStream.Seek(_dataOffset, SeekOrigin.Begin);
        }

        public int RowCount { get; private set; }

        public int Version { get; private set; }

        private int StringTableOffset { get; set; }

        public int ReadInt32()
        {
            return _reader.ReadInt32();
        }

        public long ReadInt64()
        {
            return _reader.ReadInt64();
        }

        public float ReadFloat()
        {
            return _reader.ReadSingle();
        }

        public double ReadDouble()
        {
            return _reader.ReadDouble();
        }

        public bool ReadBool()
        {
            return _reader.ReadBoolean();
        }

        public string ReadString()
        {
            var index = _reader.ReadInt32();
            return _stringTable[index];
        }

        public int[] ReadInt32Array() => ReadArray(ReadInt32);
        public long[] ReadInt64Array() => ReadArray(ReadInt64);
        public float[] ReadFloatArray() => ReadArray(ReadFloat);
        public double[] ReadDoubleArray() => ReadArray(ReadDouble);
        public bool[] ReadBoolArray() => ReadArray(ReadBool);
        public string[] ReadStringArray() => ReadArray(ReadString);

        public int[][] ReadInt32Array2D() => ReadArray2D(ReadInt32);
        public long[][] ReadInt64Array2D() => ReadArray2D(ReadInt64);
        public float[][] ReadFloatArray2D() => ReadArray2D(ReadFloat);
        public double[][] ReadDoubleArray2D() => ReadArray2D(ReadDouble);
        public string[][] ReadStringArray2D() => ReadArray2D(ReadString);

        public HashSet<int> ReadInt32HashSet() => new HashSet<int>(ReadInt32Array());
        public HashSet<long> ReadInt64HashSet() => new HashSet<long>(ReadInt64Array());
        public HashSet<string> ReadStringHashSet() => new HashSet<string>(ReadStringArray());

        public Dictionary<int, int> ReadInt32Int32Dictionary() => ReadDictionary(ReadInt32, ReadInt32);
        public Dictionary<string, int> ReadStringInt32Dictionary() => ReadDictionary(ReadString, ReadInt32);
        public Dictionary<int, string> ReadInt32StringDictionary() => ReadDictionary(ReadInt32, ReadString);
        public Dictionary<string, string> ReadStringStringDictionary() => ReadDictionary(ReadString, ReadString);

        public void Dispose()
        {
            _reader.Dispose();
        }

        private void ReadHeader()
        {
            var magic = _reader.ReadBytes(4);
            if (!ByteArrayEquals(magic, Magic))
            {
                throw new InvalidDataFormatException($"Invalid magic header: {Encoding.ASCII.GetString(magic)}");
            }

            Version = _reader.ReadUInt16();
            _reader.ReadUInt16();
            RowCount = _reader.ReadInt32();
            StringTableOffset = _reader.ReadInt32();
        }

        private void ReadColumnDefinitions()
        {
            var columnCount = _reader.ReadUInt16();
            for (var index = 0; index < columnCount; index++)
            {
                var nameLength = _reader.ReadUInt16();
                _reader.ReadBytes(nameLength);
                _reader.ReadByte();
                _reader.ReadByte();
            }
        }

        private void ReadStringTable()
        {
            _reader.BaseStream.Seek(StringTableOffset, SeekOrigin.Begin);
            var stringCount = _reader.ReadInt32();
            for (var index = 0; index < stringCount; index++)
            {
                var length = _reader.ReadUInt16();
                var bytes = _reader.ReadBytes(length);
                _stringTable[index] = Encoding.UTF8.GetString(bytes);
            }
            _dataOffset = _reader.BaseStream.Position;
        }

        private T[] ReadArray<T>(Func<T> itemReader)
        {
            var count = _reader.ReadInt32();
            var result = new T[count];
            for (var index = 0; index < count; index++)
            {
                result[index] = itemReader();
            }
            return result;
        }

        private T[][] ReadArray2D<T>(Func<T> itemReader)
        {
            var rowCount = _reader.ReadInt32();
            var rows = new T[rowCount][];
            for (var row = 0; row < rowCount; row++)
            {
                var columnCount = _reader.ReadInt32();
                var items = new T[columnCount];
                for (var column = 0; column < columnCount; column++)
                {
                    items[column] = itemReader();
                }
                rows[row] = items;
            }
            return rows;
        }

        private Dictionary<TKey, TValue> ReadDictionary<TKey, TValue>(Func<TKey> keyReader, Func<TValue> valueReader) where TKey : notnull
        {
            var count = _reader.ReadInt32();
            var result = new Dictionary<TKey, TValue>(count);
            for (var index = 0; index < count; index++)
            {
                var key = keyReader();
                var value = valueReader();
                result[key] = value;
            }
            return result;
        }

        private static bool ByteArrayEquals(byte[] left, byte[] right)
        {
            if (left.Length != right.Length)
            {
                return false;
            }

            for (var index = 0; index < left.Length; index++)
            {
                if (left[index] != right[index])
                {
                    return false;
                }
            }

            return true;
        }
    }
}
