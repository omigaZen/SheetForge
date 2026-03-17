using System;
using System.Collections;
using System.Collections.Generic;

namespace SheetForge
{
    public abstract class TableBase<T> : IEnumerable<T> where T : class
    {
        protected readonly Dictionary<long, T> _items = new Dictionary<long, T>();
        protected readonly List<T> _itemList = new List<T>();

        public abstract string TableName { get; }

        public int Count => _items.Count;

        public double LoadTimeMs { get; protected set; }

        public T? Get(long id)
        {
            _items.TryGetValue(id, out var item);
            return item;
        }

        public bool TryGet(long id, out T? item)
        {
            return _items.TryGetValue(id, out item);
        }

        public bool Contains(long id)
        {
            return _items.ContainsKey(id);
        }

        public IReadOnlyList<T> GetAll()
        {
            return _itemList;
        }

        public T this[long id] => _items[id];

        public abstract void Load(string filePath);

        public IEnumerator<T> GetEnumerator()
        {
            return _itemList.GetEnumerator();
        }

        IEnumerator IEnumerable.GetEnumerator()
        {
            return GetEnumerator();
        }
    }
}
