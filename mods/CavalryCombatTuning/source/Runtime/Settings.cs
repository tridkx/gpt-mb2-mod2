using System;
using System.IO;
using System.Xml;
using System.Xml.Serialization;

namespace CavalryCombatTuning
{
    [XmlRoot("CavalryCombatTuning")]
    public sealed class Settings
    {
        public float ChargeDamageMultiplier { get; set; } = 2.5f;
        public float MountedMovementPenaltyMultiplier { get; set; } = 0.7f;
        public bool MountedAccuracyAIOnly { get; set; } = false;

        public void Validate()
        {
            ValidateRange(ChargeDamageMultiplier, 0f, 10f, nameof(ChargeDamageMultiplier));
            ValidateRange(MountedMovementPenaltyMultiplier, 0f, 3f, nameof(MountedMovementPenaltyMultiplier));
        }

        private static void ValidateRange(float value, float min, float max, string name)
        {
            if (float.IsNaN(value) || float.IsInfinity(value) || value < min || value > max)
                throw new InvalidDataException(name + " must be between " + min + " and " + max + ".");
        }

        public static Settings Load(string path)
        {
            using (var reader = XmlReader.Create(path, new XmlReaderSettings
            {
                DtdProcessing = DtdProcessing.Prohibit,
                XmlResolver = null
            }))
            {
                var serializer = new XmlSerializer(typeof(Settings));
                serializer.UnknownNode += (sender, args) =>
                {
                    if (args.NodeType == XmlNodeType.Element)
                        throw new InvalidDataException("Unknown setting: " + args.Name);
                };
                var settings = (Settings)serializer.Deserialize(reader);
                settings.Validate();
                return settings;
            }
        }
    }
}
