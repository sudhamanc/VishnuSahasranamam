#!/usr/bin/env python3
"""Build stotram.js from source recension + simple English explanations."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_TS = ROOT / "scripts" / "source" / "vishnu.ts.txt"
NAMES_JSON = ROOT / "scripts" / "source" / "names_1000.json"
OUT = ROOT / "data" / "stotram.js"

NAME_RANGES = [
    (1, 9), (10, 17), (18, 24), (25, 36), (37, 45), (46, 55), (56, 64),
    (65, 74), (75, 85), (86, 95), (96, 104), (105, 114), (115, 123),
    (124, 133), (134, 141), (142, 151), (152, 163), (164, 173), (174, 181),
    (182, 189), (190, 198), (199, 209), (210, 219), (220, 229), (230, 237),
    (238, 248), (249, 257), (258, 266), (267, 276), (277, 284), (285, 291),
    (292, 301), (302, 309), (310, 319), (320, 328), (329, 337), (338, 347),
    (348, 356), (357, 364), (365, 374), (375, 385), (386, 395), (396, 406),
    (407, 416), (417, 426), (427, 435), (436, 445), (446, 455), (456, 465),
    (466, 475), (476, 485), (486, 493), (494, 502), (503, 512), (513, 521),
    (522, 531), (532, 539), (540, 548), (549, 560), (561, 569), (570, 577),
    (578, 589), (590, 599), (600, 608), (609, 618), (619, 627), (628, 636),
    (637, 645), (646, 654), (655, 664), (665, 674), (675, 682), (681, 691),
    (692, 700), (701, 709), (710, 718), (719, 726), (727, 738), (739, 748),
    (749, 758), (759, 766), (767, 774), (775, 783), (784, 791), (792, 801),
    (802, 808), (809, 818), (819, 827), (828, 836), (837, 848), (849, 858),
    (859, 868), (869, 877), (878, 887), (888, 896), (897, 906), (907, 915),
    (916, 923), (924, 932), (933, 941), (942, 951), (952, 960), (961, 968),
    (969, 977), (978, 986), (987, 994), (995, 1000),
]

# Shloka 72 in the source listing was 675–680 (6 names). Align to 675–682 so
# 73 can start at 681 as in the traditional grouping, then continue. The
# opensadhaka list has 72 as 675–680 and 73 as 681–691. Keep that mapping
# by overriding 72 after the fact if needed. We use the published ranges:

NAME_RANGES[71] = (675, 680)  # shloka 72

ESSENCES = [
    "The Lord is the whole universe, present in every place. He is the sacred offering, the master of past, present and future, and the one who makes, holds, and nourishes every living being.",
    "He is the pure Self and the Supreme Self. For those who are free, He is the last home. He never fades. He lives within, watches all, knows the body, and never dies.",
    "He is yoga itself and the guide of yogis. He rules both nature and the soul. He took the Narasimha form, He is glorious Keshava, and He is the highest Person.",
    "He is everything, and also the one who brings things to a close. He is auspicious, steady, the source of beings, and an unending treasure. He appears, cares, supports, and rules.",
    "He exists by Himself. He gives joy, shines like the sun, and has lotus-like eyes. He has no beginning or end. He holds the world, orders it, and is its highest support.",
    "No one can measure Him. He is the Lord of the senses, with a lotus at His navel, and Lord of the deathless ones. He shapes the universe, thinks, forms, is vast, ancient, and unmoving.",
    "The senses cannot grasp Him. He is eternal, dark-hued Krishna, red-eyed, and the one who dissolves the world. He is full, the support of the three worlds, the purifier, and the highest blessing.",
    "He governs, gives life, and is life itself. He is the eldest and the most worthy. He is the golden-wombed creator, holds the earth, is Lakshmi’s Lord, and the slayer of the demon Madhu.",
    "He is all-powerful, brave, and a bowman. He is wise, He strides through the worlds, and He is everywhere. No one is above Him. He cannot be shaken. He knows every deed and is the deed itself.",
    "He is Lord of the gods, the safe shelter, and true peace. He is the seed of the universe and the source of beings. He is day, time, hard to catch, the very knowing, and the one who sees all.",
    "He was never born. He is Lord of all, already complete, and the fulfilment of every aim. He is the first cause, the one who never falls, the dharma-bearing boar, and free of every bond.",
    "He is the home of all and of a clean mind. He is truth, even toward everyone, beyond measure, and fair. His work never fails. He is lotus-eyed, and every act of His is dharma.",
    "He is Rudra, many-headed, the bearer of all. The universe is born from Him. His fame is holy. He is immortal, eternally steady, the best refuge, and of great tapas.",
    "He is everywhere and knows everything. He shines. No army can stand before Him, and He corrects the wicked. He is the Veda, knows the Veda, is flawless, and is the seer.",
    "He watches over the worlds, the gods, and dharma. He is both the work and its cause. He has four aspects, four forms, four tusks as Narasimha, and four arms.",
    "He shines always. He is both what is enjoyed and the enjoyer. He is patient, first-born of the world, without sin, victorious, the womb of the universe, and He returns again and again.",
    "He is Upendra, the dwarf Vamana, and also the tall one. His gifts never fail. He is pure and strong, greater than Indra, the holder, the creation itself, self-held, and the one who sets the rules.",
    "He is what we should know, and the healer of worldly pain. He is always in yoga, slays great foes, is Lord of knowledge, and sweet as honey. He is beyond the senses, of great Maya, zeal, and strength.",
    "His wisdom, vigour, power, and light are boundless. His form cannot be pointed out. He is glorious, His Self cannot be measured, and He held up the great mountain.",
    "He is the mighty archer, holder of the earth, and the home of Lakshmi. The good take refuge in Him. Nothing can block Him. He is the joy of the gods, Govinda, and Lord of those who know.",
    "He is a ray of light, the subduer, the swan of wisdom, and fair-winged. He is the best of serpents, golden-naveled, of deep tapas, lotus-naveled, and Lord of creatures.",
    "He does not die. He sees all, is the lion, joins actions to their fruits, and is steady. He is unborn, hard for foes to bear, the teacher, of famous Self, and slayer of the gods’ enemies.",
    "He is the teacher, and the greatest teacher. He is the true home, the truth, and of true valour. He sleeps in yoga and is also ever awake. He wears a garland, is Lord of speech, and of a generous mind.",
    "He leads at the front and leads the hosts. He is glorious, justice itself, the guide, and the mover of all. He is thousand-headed, the Self of the universe, thousand-eyed, and thousand-footed.",
    "He turns the wheel of birth and death. His Self is turned away from the world. He is hidden, and He crushes the wicked. He is day, the fire of time, wind, and the one who holds the earth.",
    "His grace is kind and His heart is calm. He holds, protects, and fills the universe. He honours the good and is honoured. He is righteous, Narayana, and the true guide.",
    "He cannot be counted and cannot be measured. He is foremost, the leader of the good, and pure. His aims succeed, His will never fails, He gives success, and He is the way to success.",
    "He is Lord of dharma and showers blessings. He is Vishnu, whose steps are dharma. Beings come from Him. He makes us grow, is ever growing, unattached, and an ocean of the Vedas.",
    "His arms are beautiful and He is hard to hold in the mind. He is eloquent, the great Lord, giver of wealth, and wealth itself. He has many forms and a vast form, and He lights all things.",
    "He bears strength, heat, and radiance. His Self is light. He is full. The syllable Om is His. He is the sacred mantra, cool as moonlight, and bright as the sun.",
    "The moon was born from Him. He shines, is marked like the moon, and is Lord of the gods. He is the medicine for worldly pain, the bridge across it, and true in both dharma and courage.",
    "He is Lord of what was, what is, and what will be. He is wind, the purifier, and fire. He ends selfish desire, also fulfils right desire, is the beloved, the longed-for, and the giver of blessings.",
    "He starts the ages and turns them. His Maya has many forms. He is the great devourer at the end. He cannot be seen, yet He also shows a form. He conquers thousands, and the endless.",
    "He is loved, lives equally in all, and is dear to the wise. He is the crested one, the binder, and dharma itself. He ends anger, stirs courage against harm, does all, and holds the earth.",
    "He never falls. He is famous, the life-breath, and the giver of life. He is Indra’s younger brother, the ocean, the ground of all, always watchful, and firmly established.",
    "He is Skanda, the bearer of the load, the giver of boons, and the mover of the winds. He is Vasudeva, of vast light, the first God, and the breaker of enemy forts.",
    "He is without sorrow, the one who ferries us across, and the saviour. He is brave, son of Shura, Lord of people, always kind, of many births, lotus-handed, and lotus-eyed.",
    "He is lotus-naveled and lotus-eyed, worshipped in the heart-lotus, and the one who holds bodies. He is rich in glory, complete, the ancient Self, wide-eyed, and His banner is Garuda.",
    "No one is like Him. He is awe-inspiring, knows the right time, and receives the offering. All true signs point to Him. He is Lakshmi’s Lord, and He wins every battle.",
    "He does not decay. He is the red one (the fish), the path, and the cause. He is Damodara, patient, holder of the earth, greatly blessed, swift, and of endless appetite at the world’s end.",
    "All things rise from Him. He stirs nature into creation. He is God, glory lives in Him, and He is the supreme Lord. He is the tool, the cause, the doer, the maker of many, deep, and hidden.",
    "He is firm resolve and the order that holds things. He is the final home, the giver of a place, and the fixed one. He is supremely rich, clearly seen, content, full, and of a kind glance.",
    "He is Rama, the resting place, and without stain. He is the path, the one who is led and the one who leads — yet no one leads Him. He is the hero, dharma itself, and the best knower of dharma.",
    "He is Lord of Vaikuntha, the Purusha, the breath of life, and the giver of life. He is the sacred Om, the wide one, the golden-wombed, slayer of foes, all-pervading, wind, and never fallen.",
    "He is the seasons, of blessed sight, and time itself. He sits in the highest place and receives worship. He is fierce when needed, the year, skilled, the resting place, and able in all things.",
    "He is the vast expanse, the still support, and the very proof. He is the seed that never dies. He is the true goal, needs nothing, holds great treasure, great joy, and great wealth.",
    "He never loses heart. He is vast and unborn. He is the post of dharma and the great sacrifice. He is the hub of the stars, lord of the stars, able, pure, and of good will.",
    "He is the sacrifice, the one worshipped, and the one most worthy of worship. He is the rite, the long session of offering, and the goal of the good. He sees all, is free, knows all, and is the highest knowledge.",
    "His vows are noble, His face is kind, and He is subtle. His sound is holy, He gives joy, and He is a true friend. He wins the heart, has conquered anger, has heroic arms, and tears down evil.",
    "He sends beings into sleep, is His own master, and fills all space. He has many selves and does many works. He is the year, full of love, a protector, jewel-wombed, and Lord of wealth.",
    "He guards dharma, does dharma, and is dharma. He is the real and the unreal, the passing and the lasting. As witness He does not ‘know’ as we do. He is thousand-rayed, the ordainer, and of a clear nature.",
    "He is the hub of light, seated in goodness, the lion, and great Lord of beings. He is the first God, the great God, Lord of the gods, their support, and their teacher.",
    "He is the highest, Lord and protector of the earth. He is reached through knowledge and is most ancient. He holds the body’s elements, is the enjoyer, Lord of the monkeys as Rama, and a generous giver.",
    "He drinks the Soma and the nectar. He is the moon, conqueror of many, and best among beings. He humbles pride, is victory, keeps His word, is of the Dasharha line, and Lord of the Satvatas.",
    "He is the living Self, the one who trains, and the witness. He is Mukunda, who gives freedom, of endless stride, the ocean, of infinite Self, resting on the waters, and the end of all.",
    "He is unborn, worthy of great worship, and always Himself. He conquers enemies and is full of joy. He is bliss, the one who delights, the complete, true to dharma, and the one who took three strides.",
    "He is the great seer, the teacher Kapila, and knower of all that is done. He is Lord of the earth, of three steps, overseer of the gods, the great-horned fish, and the ender of death.",
    "He is the great boar, Govinda, with a good army, wearing golden armlets. He is secret, deep, hard to enter, hidden, and He holds the discus and the mace.",
    "He creates, acts through His own limbs, and cannot be conquered. He is Krishna, firm, who draws all in, and never falls. He is Varuna, the steadfast tree, lotus-eyed, and great-minded.",
    "He is the Blessed Lord, who withdraws glory at the end, and is always blissful. He wears the forest garland, holds the plough as Balarama, is the sun’s radiance, patient, and the highest goal.",
    "He holds the good bow Sharnga and the axe as Parashurama. He is stern to the wicked and generous with wealth. He touches heaven, sees all, is Vyasa, Lord of learning, and not born of a womb.",
    "The three Sama hymns praise Him. He sings the Sama and is the Sama. He is freedom, the medicine, and the physician. He taught renunciation, is calm, peace itself, and the last refuge.",
    "His form is beautiful. He gives peace and creates. He delights in the earth and rests on the waters. He is the friend, Lord, and protector of the earth (and of cows). His eyes bless, and He loves dharma.",
    "He never turns back from what is right. His Self is withdrawn from the world. He draws the universe in, does good, and is auspicious. He bears the Srivatsa, is Lakshmi’s home, her Lord, and the best of the glorious.",
    "He gives prosperity, is Lakshmi’s Lord, her home, and her treasure. He shares fortune, bears her, makes well-being, is the highest good, the glorious one, and the shelter of the three worlds.",
    "His eyes and limbs are beautiful. He is endless bliss, joy itself, and Lord of the lights. He has mastered the mind, is under no one’s command, of true fame, and free of doubt.",
    "He is risen above all, the eye in every place, and has no master. He is eternally still. He rests on the earth, is its ornament and its being, without sorrow, and the one who takes sorrow away.",
    "He is radiant and worshipped, the vessel of all, of a pure Self, and the purifier. He is Aniruddha, a warrior without rival, Pradyumna, and of measureless valour.",
    "He slew Kalanemi. He is the hero, son of Shura, and Lord of the brave. He is the Self and Lord of the three worlds, Keshava, slayer of the demon Keshi, and Hari who removes pain.",
    "He is the desired God, the keeper of wishes, fulfilled, and lovely. He gave the scriptures. His form cannot be described. He is Vishnu, the hero, the endless, and Dhananjaya.",
    "He loves the Vedas and the good. He makes Brahman, is Brahma, is Brahman, and makes the Vedas grow. He knows the Veda, is the Brahmana, holds Brahman, knows Brahman, and is dear to the Brahmanas.",
    "His stride is great, His work is great, His light is great. He is the great serpent. He is the great rite, the great sacrificer, the great yajna, and the great offering.",
    "He is worthy of praise, loves praise, and is the hymn, the praise, and the one who praises. He loves the fight that protects. He is full, He fills others, He is holy, of holy fame, and free from illness.",
    "He is swift as thought and makes holy crossings. His essence is gold. He gives wealth, and also the wealth of freedom. He is Vasudeva, the abode, of a noble mind, and the offering itself.",
    "He is the path of the good, their noble work, pure being, true glory, and their highest aim. He has a heroic army, is best of the Yadus, the home of the good, and lives by the Yamuna.",
    "Beings live in Him. He is Vasudeva, the home of every life-breath, and of endless power. He breaks false pride, gives true dignity, is content, hard to hold, and never defeated.",
    "His form is the universe, vast, and shining — and He is also without form. He has many forms, is unmanifest, of a hundred forms, and of a hundred faces.",
    "He is the One, and also the many. He is the sacrifice, the ‘who’, the ‘what’, and the highest ‘That’. He is the friend and Lord of the world, Madhava, and tender toward His devotees.",
    "He is golden in colour and in limb, of a beautiful body, and adorned with sandal. He slays foes, is without equal, empty of selfish qualities, free of craving, still, and also moving.",
    "He has no pride, gives honour, and is worthy of honour. He is Lord of the worlds and holds the three worlds. He is wise, born of sacrifice, blessed, of true insight, and holder of the earth.",
    "He rains splendour and wears light. He is the best of those who bear weapons. He accepts devotion, restrains, and is always intent on His people. He has many forms, and is Gada’s elder brother.",
    "He has four forms, four arms, four vyuhas, and is the fourfold goal. He has a fourfold Self, gives the four aims of life, knows the four Vedas, and stands as one transcendent foot.",
    "He turns the cycle well. His Self never fails. He is hard to defeat, hard to overstep, hard to reach, hard to know, a hard fort to cross, hard to house in the heart, and slayer of cruel foes.",
    "His form is auspicious. He draws the essence of the worlds. He is the fine thread of creation and makes it grow. His deeds are like Indra’s, great, already complete, and He gave the scriptures.",
    "He is the source, beautiful, and gentle. His navel is a jewel, His eyes are lovely. He is worthy of worship, giver of food, the horned one, the victor, and the all-knowing conqueror.",
    "He is the golden syllable, unshaken, and Lord of all who master speech. He is the great lake of bliss, the great deep, the great being, and the great treasure.",
    "He delights in the earth, is pure as jasmine, white, and the rain-cloud. He purifies, needs no breath, lives on nectar, has an immortal body, knows all, and has faces on every side.",
    "Devotees reach Him easily. His vows are good, He is already accomplished, He conquers enemies and burns them away. He is the banyan, the udumbara, the peepal, and the slayer of Chanura.",
    "He has a thousand rays, seven tongues of fire, seven flames, and the seven horses of the sun. He is without form, without sin, beyond thought. He frightens the wicked and removes the fear of the good.",
    "He is the smallest and the largest, the thin and the stout. He bears the gunas and is also beyond them. He is the Great. No one holds Him; He holds Himself. His face is fair, His line is ancient, and He makes the line grow.",
    "He bears the world’s burden. The Vedas speak of Him. He is the yogi and Lord of yogis, giver of every wish, the resting place, who wearies the wicked, fair-winged, and borne by the wind.",
    "He holds the bow and knows the science of the bow. He is the rod of justice, the one who tames, and self-control itself. He cannot be defeated, bears all, sets the law, is bound by no law, and is not death.",
    "He is full of sattva, lives in sattva, and is the truth. He is devoted to truth and dharma. He is the aim all hearts want, worthy of love and worship, doer of what is dear, and increaser of love.",
    "His path is the sky. He is light, of lovely glow, enjoyer of the offering, and all-pervading. He is the sun that draws, the shining one, the sun, the impeller, and His eye is the sun.",
    "He is endless, enjoyer of the offering, and the enjoyer. He gives joy, is born many times, and is the first-born. He never despairs, is always patient, the support of the worlds, and wonderful.",
    "He is from of old, the most eternal, the tawny sage Kapila, the sun, and the unchanging. He gives well-being, makes well-being, is well-being, enjoys it, and bestows it as a blessing.",
    "He is without cruelty, wears earrings, and holds the discus. He is valiant, of strong rule, beyond words, the meaning of all words, the cool refuge, and the maker of night at the end.",
    "He is not cruel, He is graceful, skilled, and generous. He is the best of the patient, the most learned, without fear, and even hearing His names is a holy act.",
    "He lifts us across, destroys bad deeds, is holy, and ends bad dreams. He slays foes, protects, lives in the good, is the life of all, and is present everywhere.",
    "His forms are endless, His glory is endless. He has conquered anger and takes fear away. He is just, of a deep Self, the one who shares the fruits, the commander, and the very directions.",
    "He has no beginning. He is the earth’s support and the glory of all. He is a true hero, of shining armlets, the father of beings, their source, awe-inspiring, and of terrible valour to the wicked.",
    "He is the base of every base, and no one is above Him. Creation opens like a flower. He is always awake, always rising, walks the good path, gives life, is the Om, and the just rewarder.",
    "He is the true measure, the home of the breath, the holder of the breath, and the life of the vital airs. He is Reality, knower of Reality, the one Self, and beyond birth, death, and old age.",
    "He is the tree of the three worlds, the saviour, the impeller, and the grandfather of all. He is the sacrifice, its Lord, the sacrificer, its limbs, and the one who carries it.",
    "He holds the sacrifice, performs it, owns it, eats the offering, and is its means. He completes it, is its secret, and is both the food and the one who eats the food.",
    "He is His own source and self-born. As the boar He lifted the earth. He sings the Sama, is Devaki’s delight, the creator, Lord of the earth, and the destroyer of sin.",
    "He holds the conch, the sword Nandaka, the discus, the bow Sharnga, and the mace. He holds the wheel in His hand, cannot be shaken, and every weapon is His.",
    "May the glorious Narayana — Vishnu, Vasudeva — who wears the forest garland and holds the mace, the Sharnga bow, the conch, the discus, and the sword, always protect us.",
]


DHYANA_EN = {
    0: "In the milk ocean, on a gem-bright shore, seated on a throne of pearls, shining like crystal, with nectar raining from white clouds — may that joyful Mukunda, holding lotus, mace, and conch, make us pure.",
    1: "The earth is His feet, space His navel, wind His breath, sun and moon His eyes, the directions His ears, heaven His head, fire His mouth, the ocean His belly. The three worlds are His body. I bow to that Vishnu.",
    2: "Om. Salutation to the Blessed Lord Vasudeva.",
    3: "Of peaceful form, resting on the serpent, lotus-naveled, Lord of the gods, support of the universe, wide as the sky, dark as a cloud, Lakshmi’s beloved, lotus-eyed — I bow to Vishnu, who takes away the fear of this world.",
    4: "Dark as a rain-cloud, wearing yellow silk, marked with Srivatsa, shining with the Kaustubha gem, full of goodness, with wide lotus eyes — I bow to Vishnu, the one Lord of all worlds.",
    5: "Salutation to the first of all beings, the holder of the earth, who takes countless forms — to Vishnu, the all-powerful.",
    6: "With conch and discus, crown and earrings, yellow cloth, lotus eyes, and the Kaustubha on His chest — I bow my head to the four-armed Vishnu.",
    7: "In the shade of the Parijata tree, on a golden throne, dark as a cloud, moon-faced, four-armed, with Rukmini and Satyabhama — I take refuge in Krishna.",
}

OPENING_EN = {
    "शुक्लाम्बरधरं": "Meditate on Vishnu in white, moon-bright, four-armed, with a peaceful face, so that every obstacle may settle.",
    "यस्य द्विरदवक्त्राद्याः": "I take refuge in Vishvaksena, whose elephant-faced attendants always destroy obstacles.",
    "व्यासं वसिष्ठनप्तारं": "I bow to Vyasa, grandson of Shakti, son of Parashara, father of Shuka, a treasure of tapas.",
    "व्यासाय विष्णुरूपाय": "Salutation to Vyasa, who is Vishnu’s form, and to Vishnu, who is Vyasa’s form — treasure of Brahman, of Vasishtha’s line.",
    "अविकाराय शुद्धाय": "Salutation to Vishnu, unchanged, pure, eternal, the Supreme Self, of one form always, victorious over all.",
    "यस्य स्मरणमात्रेण": "Even remembering Him frees a person from the knot of birth and worldly life. Salutation to that all-powerful Vishnu.",
    "विष्णुं जिष्णुं महाविष्णुं": "I bow to the Supreme Person — Vishnu, the victorious, the great Vishnu, the powerful, the great Lord, who takes many forms and ends the demons.",
}

# Verses M. S. Subbulakshmi sings before the thousand names (not the Mahābhārata dialogue).
OPENING_PREFIXES = tuple(OPENING_EN.keys())

PHALA_EN = {
    "इतीदं कीर्तनीयस्य": "Thus the thousand divine names of the great Keshava, worthy of praise, have been fully told.",
    "य इदं शृणुयान्नित्यं": "Whoever hears this every day, and whoever recites it, meets no harm here or in the world after.",
    "रोगार्तो मुच्यते": "The sick are freed from illness, the bound from bondage, the frightened from fear, and the distressed from danger.",
    "न वासुदेवभक्तानामशुभं": "For devotees of Vasudeva, nothing inauspicious remains — not the fear of birth, death, old age, or disease.",
    "श्रीरामरामरामेति": "O fair-faced one, I delight in the name Rama, Rama, Rama. That one name is equal to the whole thousand names.",
    "आर्ता विषण्णाः": "The hurting, the weary, the shaken, and the sick become free of sorrow and find joy by simply saying the name Narayana.",
    "कायेन वाचा मनसेन्द्रियैर्वा": "Whatever I do with body, speech, mind, senses, intellect, or nature — I offer it all to Narayana.",
    "परित्राणाय साधूनां": "To protect the good, to end the wicked, and to set dharma on its feet, I am born age after age.",
}


def extract_section(text: str, key: str) -> list[dict[str, str]]:
    m = re.search(rf'key: "{key}".*?verses: \[(.*?)\n \],', text, re.S)
    if not m:
        raise SystemExit(f"section {key} not found")
    pairs = re.findall(r'devanagari: "(.*?)", iast: "(.*?)"', m.group(1))
    out = []
    for sa, iast in pairs:
        sa = sa.replace("विनियोज्यः", "").replace(" viniyojyaḥ", "").strip()
        iast = iast.replace(" viniyojyaḥ", "").strip()
        out.append({"sa": sa, "iast": iast})
    return out


def simplify_meaning(text: str) -> str:
    t = text.strip()
    t = re.sub(r"^He who is ", "", t, flags=re.I)
    t = re.sub(r"^He who ", "", t, flags=re.I)
    t = t[0].upper() + t[1:] if t else t
    if not t.endswith("."):
        t += "."
    return t


def is_speaker(sa: str) -> bool:
    return "उवाच" in sa and "।" not in sa and len(sa) < 40


def is_om_iti(sa: str) -> bool:
    return "ॐ नम इति" in sa or sa.endswith("ॐ नमः ॥")


def pick_en(sa: str, table: dict[str, str], fallback: str) -> str:
    for key, val in table.items():
        if sa.startswith(key) or key in sa[:24]:
            return val
    return fallback


def main() -> None:
    text = SRC_TS.read_text(encoding="utf-8")
    names_raw = json.loads(NAMES_JSON.read_text(encoding="utf-8"))
    names_by_n = {int(x["n"]): x for x in names_raw}

    purva = extract_section(text, "purva")
    dhyana = extract_section(text, "dhyana")
    stotram = extract_section(text, "stotram")
    phala = extract_section(text, "phalashruti")

    # Stotram verses: skip harih om prefix-only extras after 108
    name_verses = []
    extras = []
    for i, v in enumerate(stotram):
        sa = v["sa"]
        if sa.startswith("हरिः ॐ") or re.search(r"॥\s*[१]?[०-९]+॥", sa) or "वनमाली" in sa:
            if "ॐ नम इति" in sa or sa.startswith("सर्वप्रहरणायुध ॐ") or sa.startswith("श्रीवासुदेवोऽभिरक्षतु ॐ"):
                extras.append(v)
            else:
                name_verses.append(v)
        else:
            extras.append(v)

    # Keep first 108 name shlokas (1–107 numbered + vanamali as 108)
    # The source has: 107 numbered, then om nama iti, then 108 vanamali, then om nama iti
    numbered = []
    vanamali = None
    for v in name_verses:
        if v["sa"].startswith("वनमाली"):
            vanamali = v
        else:
            numbered.append(v)

    if len(numbered) < 107:
        raise SystemExit(f"expected 107 numbered shlokas, got {len(numbered)}")
    numbered = numbered[:107]
    if vanamali is None:
        raise SystemExit("vanamali verse missing")

    opening_verses = [
        v for v in purva if any(v["sa"].startswith(p) for p in OPENING_PREFIXES)
    ]
    if not opening_verses:
        raise SystemExit("opening verses (Śuklāmbaradharam…) not found")

    learn = []
    listen = []

    def add_learn(section: str, v: dict, en: str, names=None):
        item = {
            "id": f"{section}-{len(learn)+1:03d}",
            "n": len(learn) + 1,
            "section": section,
            "sa": v["sa"],
            "iast": v["iast"],
            "en": en,
            "names": names or [],
        }
        if section == "stotram":
            item["shloka"] = sum(1 for x in learn if x["section"] == "stotram") + 1
        learn.append(item)
        listen.append(
            {
                "section": section,
                "sa": item["sa"],
                "iast": item["iast"],
                "en": item["en"],
                "weight": 2.2 if len(item["sa"]) > 120 else 1.15 if section != "stotram" else 1.0,
                "learnId": item["id"],
            }
        )

    for v in opening_verses:
        add_learn("opening", v, pick_en(v["sa"], OPENING_EN, "An opening verse of the recitation."))

    for i, v in enumerate(dhyana):
        if is_speaker(v["sa"]) or is_om_iti(v["sa"]):
            continue
        add_learn(
            "dhyana",
            v,
            DHYANA_EN.get(i, "A meditation verse on the form of Vishnu."),
        )

    for i, v in enumerate(numbered):
        start, end = NAME_RANGES[i]
        names = []
        for n in range(start, end + 1):
            item = names_by_n[n]
            names.append(
                {
                    "n": n,
                    "name": item["name"],
                    "en": simplify_meaning(item["meaning"]),
                }
            )
        sa = re.sub(r"^हरिः ॐ । ॐ ", "", v["sa"])
        iast = re.sub(r"^hariḥ oṃ \| oṃ ", "", v["iast"])
        add_learn("stotram", {"sa": sa, "iast": iast}, ESSENCES[i], names)
    add_learn("stotram", vanamali, ESSENCES[107], [])

    for v in phala:
        sa = v["sa"]
        if is_speaker(sa) or is_om_iti(sa):
            continue
        listen.append(
            {
                "section": "phalashruti",
                "sa": sa,
                "iast": v["iast"],
                "en": pick_en(
                    sa,
                    PHALA_EN,
                    "A closing verse on the fruit of hearing and reciting these names.",
                ),
                "weight": 1.6 if len(sa) > 140 else 1.0,
            }
        )

    payload = {
        "meta": {
            "titleSa": "श्रीविष्णुसहस्रनामस्तोत्रम्",
            "titleEn": "Śrī Viṣṇu Sahasranāmam",
            "subtitle": "A quiet companion for learning the thousand names, one verse at a time.",
            "source": "Mahabharata, Anushasana Parva. Recension commonly recited with Shankara’s tradition.",
            "audioNote": "M. S. Subbulakshmi’s recitation is still under copyright, so it is not bundled here. Load your own copy of her recording (many households already have it). The listen view will scroll with the audio.",
            "reciter": "M. S. Subbulakshmi",
            "timing": {
                "id": "mss-from-shuklam",
                "label": "M. S. Subbulakshmi — from Śuklāmbaradharam (~30 min)",
                "expectedDuration": 1790,
                "namesStart": 200,
                "namesEnd": 1240,
            },
            "stotramCount": 108,
        },
        "learn": learn,
        "listen": listen,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        "window.STOTRAM = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print(f"learn={len(learn)} listen={len(listen)} -> {OUT}")


if __name__ == "__main__":
    main()
