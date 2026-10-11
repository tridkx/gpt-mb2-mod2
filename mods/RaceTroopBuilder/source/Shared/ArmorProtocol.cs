#nullable disable
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Xml;
using System.Xml.Linq;

namespace RaceTroopBuilder.Armor
{
    public class ArmorValues
    {
        public int Head { get; set; }
        public int Body { get; set; }
        public int Arms { get; set; }
        public int Legs { get; set; }
        public int Get(int part) { return part == 0 ? Head : part == 1 ? Body : part == 2 ? Arms : Legs; }
    }

    // Shared by desktop validation and the game runtime. No dependency on game assemblies.
    public static class ArmorProtocol
    {
        public const string RaceFile = "rtb_race_armor.xml";
        public const string TroopFile = "rtb_troop_armor.xml";
        public static XElement WriteValues(string element, ArmorValues values)
        {
            return new XElement(element, new XAttribute("head", values.Head), new XAttribute("body", values.Body),
                new XAttribute("arms", values.Arms), new XAttribute("legs", values.Legs));
        }
        public static ArmorValues ReadValues(XElement element)
        {
            var v = new ArmorValues();
            var names = new[] { "head", "body", "arms", "legs" };
            var values = new int[4];
            for (int i = 0; i < 4; i++)
                if (!int.TryParse((string)element.Attribute(names[i]), NumberStyles.None, CultureInfo.InvariantCulture, out values[i]) || values[i] > 500)
                    throw new InvalidDataException("护甲必须为 0～500 的整数，且四部位齐全：" + names[i]);
            v.Head = values[0]; v.Body = values[1]; v.Arms = values[2]; v.Legs = values[3];
            return v;
        }
        public static XElement ReadRoot(string path, string expected)
        {
            using (var reader = XmlReader.Create(path, new XmlReaderSettings { DtdProcessing = DtdProcessing.Prohibit, XmlResolver = null }))
            {
                var root = XDocument.Load(reader).Root;
                if (root == null || root.Name != expected || (string)root.Attribute("schemaVersion") != "1")
                    throw new InvalidDataException("护甲协议根节点或版本错误：" + path);
                return root;
            }
        }
        public static Dictionary<string, ArmorValues> ReadRaces(string path)
        {
            var result = new Dictionary<string, ArmorValues>(StringComparer.Ordinal);
            if (!File.Exists(path)) return result;
            foreach (var race in ReadRoot(path, "RaceArmor").Elements())
            {
                var id = (string)race.Attribute("id");
                if (race.Name != "Race" || string.IsNullOrWhiteSpace(id) || result.ContainsKey(id))
                    throw new InvalidDataException("种族护甲 ID 为空、重复或节点错误：" + path);
                result.Add(id, ReadValues(race));
            }
            return result;
        }
    }
}
