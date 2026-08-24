#!/usr/bin/env python3
"""Build stotram.js from source recension + simple English explanations."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_TS = ROOT / "scripts" / "source" / "vishnu.ts.txt"
NAMES_JSON = ROOT / "scripts" / "source" / "names_1000.json"
TIMING_JSON = ROOT / "scripts" / "source" / "mss_timing.json"
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

# Opening verses in her recitation, keyed by purva source index.
# She does NOT sing index 0 (oṃ śrīparamātmane), 1 (atha sakala…) or 3 (Vishvaksena).
OPENING_IDX = [2, 4, 5, 6, 7]
OPENING_EN = [
    "Meditate on Vishnu in white, moon-bright, four-armed, with a peaceful face, so that every obstacle may settle.",
    "I bow to Vyasa, grandson of Vasishtha and Shakti, son of Parashara, father of Shuka, a treasure of tapas.",
    "Salutation to Vyasa, who is Vishnu’s form, and to Vishnu, who is Vyasa’s form — treasure of Brahman, of Vasishtha’s line.",
    "Salutation to Vishnu, unchanged, pure, eternal, the Supreme Self, of one form always, victorious over all.",
    "Even remembering Him frees a person from the knot of birth and worldly life. Salutation to that all-powerful Vishnu. Om, salutation to Vishnu, the all-powerful.",
]

# Pūrva pīṭhikā dialogue as she sings it: (source indices to merge, English).
PURVA_ITEMS = [
    ((9, 10), "Vaishampayana said: having heard all the purifying teachings on dharma, Yudhishthira asked Bhishma, son of Shantanu, once more."),
    ((11, 12), "Yudhishthira asked: who is the one deity in the world? What is the one highest refuge? Praising whom, worshipping whom, do people reach what is good?"),
    ((13,), "Which dharma, in your view, is the highest of all? Chanting what may a soul go free from the bonds of birth and this world?"),
    ((14, 15), "Bhishma said: the person who, always rising, praises with the thousand names the Lord of the world, God of gods, endless and supreme —"),
    ((16,), "— and who always worships that unchanging Person with devotion: meditating on Him, praising Him, bowing to Him, offering to Him —"),
    ((17,), "— praising Vishnu, who has no beginning or end, the great Lord and overseer of all worlds, that person passes beyond all sorrow."),
    ((18,), "Devoted to the Veda, knower of every dharma, He increases the fame of the worlds — Lord of the worlds, the great being, the origin of all beings."),
    ((19,), "This I hold the highest of all dharmas: that a person always worship the lotus-eyed Lord with devotion and with hymns."),
    ((20,), "He who is the highest light, the highest austerity, the highest Brahman — He is the highest refuge."),
    ((21,), "The purest of the pure, the most auspicious of the auspicious, God of gods, the undying father of all beings."),
    ((22,), "From whom all beings arise at the dawn of the first age, and in whom they dissolve again when the age ends."),
    ((23,), "Hear from me, O king, the thousand names of that Vishnu, foremost Lord of the world — names that carry away sin and fear."),
    ((24,), "Those names, famed and sung by the seers for the great-souled one, I will recount for well-being."),
    ((25,), "The seer of the thousand names is Vedavyasa, the great sage; the metre is anushtubh; the deity is the Lord, son of Devaki."),
    ((26,), "The seed is the moon-born one, the power is Devaki’s son, the heart is Trisama. It is employed for the sake of peace."),
    ((27,), "I bow to the Supreme Person — Vishnu, the victorious, the great Vishnu, the powerful, the great Lord, who takes many forms and ends the demons."),
]

NYASA = {
    "sa": "अस्य श्रीविष्णोर्दिव्यसहस्रनामस्तोत्रमहामन्त्रस्य । श्रीवेदव्यासो भगवानृषिः । अनुष्टुप् छन्दः । श्रीमहाविष्णुः परमात्मा श्रीमन्नारायणो देवता । अमृतांशूद्भवो भानुरिति बीजम् । देवकीनन्दनः स्रष्टेति शक्तिः । उद्भवः क्षोभणो देव इति परममन्त्रः । शङ्खभृन्नन्दकी चक्रीति कीलकम् । शार्ङ्गधन्वा गदाधर इत्यस्त्रम् । रथाङ्गपाणी रक्षोभ्य इति नेत्रम् । त्रिसामा सामगः सामेति कवचम् । आनन्दं परब्रह्मेति योनिः । ऋतुः सुदर्शनः काल इति दिग्बन्धः । श्रीविश्वरूप इति ध्यानम् । श्रीमहाविष्णुप्रीत्यर्थे सहस्रनामजपे विनियोगः ॥",
    "iast": "asya śrīviṣṇordivyasahasranāmastotramahāmantrasya | śrīvedavyāso bhagavānṛṣiḥ | anuṣṭup chandaḥ | śrīmahāviṣṇuḥ paramātmā śrīmannārāyaṇo devatā | amṛtāṃśūdbhavo bhānuriti bījam | devakīnandanaḥ sraṣṭeti śaktiḥ | udbhavaḥ kṣobhaṇo deva iti paramamantraḥ | śaṅkhabhṛnnandakī cakrīti kīlakam | śārṅgadhanvā gadādhara ityastram | rathāṅgapāṇī rakṣobhya iti netram | trisāmā sāmagaḥ sāmeti kavacam | ānandaṃ parabrahmeti yoniḥ | ṛtuḥ sudarśanaḥ kāla iti digbandhaḥ | śrīviśvarūpa iti dhyānam | śrīmahāviṣṇuprītyarthe sahasranāmajape viniyogaḥ ||",
    "en": "The nyasa, the ritual frame of the mantra: its seer is Vedavyasa, its metre anushtubh, its deity the great Vishnu, Narayana himself. Its seed, power, heart, armour, weapon, eye and protection are drawn from the names themselves, and it is employed in recitation to please the great Vishnu.",
}

# Phalaśruti as she sings it: (source indices to merge, English).
PHALA_ITEMS = [
    ((1,), "Thus the thousand divine names of the great Keshava, worthy of praise, have been fully told."),
    ((2,), "Whoever hears this every day, and whoever recites it, meets no harm here or in the world after."),
    ((3,), "By this a brahmana reaches the end of the Veda, a kshatriya gains victory, a vaishya wealth, a shudra happiness."),
    ((4,), "The seeker of dharma gains dharma, the seeker of wealth gains wealth, the seeker of pleasures gains them, and the seeker of children gains children."),
    ((5,), "Whoever, devoted, rising early and pure in heart, recites these thousand names of Vasudeva —"),
    ((6,), "— wins wide fame, first place among kin, unshakable prosperity, and the highest good."),
    ((7,), "Fear finds that person nowhere. Courage and radiance come, freedom from illness, beauty, strength, and character."),
    ((8,), "The sick are freed from illness, the bound from bondage, the frightened from fear, and the distressed from danger."),
    ((9,), "One who praises the Supreme Person with the thousand names, ever joined with devotion, swiftly crosses every difficulty."),
    ((10,), "A mortal who takes refuge in Vasudeva, devoted to Him, is cleansed of every sin and reaches the eternal Brahman."),
    ((11,), "For devotees of Vasudeva, nothing inauspicious remains — not the fear of birth, death, old age, or disease."),
    ((12,), "Whoever recites this hymn with faith and devotion gains happiness of self, patience, prosperity, steadiness, memory, and fame."),
    ((13,), "No anger, no envy, no greed, no impure thought remain in those devotees of the Supreme Person who have earned merit."),
    ((14,), "The sky with moon, sun and stars, the directions, the earth and the great ocean are upheld by the power of the great-souled Vasudeva."),
    ((15,), "With gods, demons and gandharvas, with yakshas, serpents and rakshasas — this whole world moves under Krishna’s sway."),
    ((16,), "The senses, mind, intellect, vitality, radiance, strength and firmness have Vasudeva as their self; He is the field and its knower."),
    ((17,), "Right conduct comes first in all scriptures; dharma is born of conduct, and the Lord of dharma is Achyuta."),
    ((18,), "The seers, the ancestors, the gods, the great elements, the substances — this whole moving and unmoving world is born of Narayana."),
    ((19,), "Yoga and its knowledge, sankhya, the arts, the Vedas, the scriptures, all knowing — all of it comes from Janardana."),
    ((20,), "Vishnu is the one great being appearing as the many. Pervading the three worlds, He, the Self of beings, enjoys all, undying."),
    ((21,), "Whoever wishes happiness and the good should recite this hymn to the Lord Vishnu, sung by Vyasa."),
    ((22, 23), "Those who worship the lotus-eyed Lord of the universe — unborn, undying master of the world — never come to defeat."),
    ((24, 25), "Arjuna said: O wide lotus-eyed one, lotus-naveled, best of gods — be the refuge of the devotees who love You, Janardana."),
    ((26, 27), "The Blessed Lord said: whoever wishes to praise Me with the thousand names, Pandava — know that I am fully praised by one verse alone. There is no doubt."),
    ((28, 29, 30), "Vyasa said: the three worlds are pervaded by the dwelling of Vasudeva. O Vasudeva, You are the home of all beings — salutation to You."),
    ((31,), "Parvati asked: by what simple means may the wise recite the thousand names of Vishnu each day? I wish to hear it, Lord."),
    ((32, 33, 34), "Shiva said: O fair-faced one, I delight in the name Rama, Rama, Rama. That one name is equal to the whole thousand names."),
    ((35, 36), "Brahma said: salutation to You, the endless one of a thousand forms, a thousand feet, eyes, heads and arms — the eternal Person, bearer of a thousand crores of ages."),
    ((38, 39), "Sanjaya said: where Krishna, the Lord of yoga, is, and where Arjuna the archer is — there are fortune, victory, prosperity, and firm justice."),
    ((40,), "The Blessed Lord said: for those who think of nothing else and worship Me all around, ever joined with Me — I carry what they need and protect what they have."),
    ((41,), "To protect the good, to end the wicked, and to set dharma on its feet, I am born age after age."),
    ((42,), "The hurting, the weary, the shaken, and the sick become free of sorrow and find joy by simply saying the name Narayana."),
    ((43,), "Whatever I do with body, speech, mind, senses, intellect, or nature — I offer it all to Narayana."),
]


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


def merge_verses(verses: list[dict], idxs: tuple) -> dict:
    sa = " ".join(verses[i]["sa"].strip() for i in idxs)
    iast = " ".join(verses[i]["iast"].strip() for i in idxs)
    return {"sa": sa, "iast": iast}


def main() -> None:
    text = SRC_TS.read_text(encoding="utf-8")
    names_raw = json.loads(NAMES_JSON.read_text(encoding="utf-8"))
    names_by_n = {int(x["n"]): x for x in names_raw}
    timing = json.loads(TIMING_JSON.read_text(encoding="utf-8"))
    cues = timing["cues"]

    purva = extract_section(text, "purva")
    dhyana = extract_section(text, "dhyana")
    stotram = extract_section(text, "stotram")
    phala = extract_section(text, "phalashruti")

    # Stotram verses: keep the 107 numbered shlokas + vanamali as 108
    name_verses = []
    for v in stotram:
        sa = v["sa"]
        if sa.startswith("हरिः ॐ") or re.search(r"॥\s*[१]?[०-९]+॥", sa) or "वनमाली" in sa:
            if "ॐ नम इति" in sa or sa.startswith("सर्वप्रहरणायुध ॐ") or sa.startswith("श्रीवासुदेवोऽभिरक्षतु ॐ"):
                continue
            name_verses.append(v)

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

    learn = []

    def add(section: str, v: dict, en: str, cue, names=None):
        item = {
            "id": f"{section}-{len(learn)+1:03d}",
            "n": len(learn) + 1,
            "section": section,
            "sa": v["sa"],
            "iast": v["iast"],
            "en": en,
            "start": cue[0],
            "end": cue[1],
            "names": names or [],
        }
        if section == "stotram":
            item["shloka"] = sum(1 for x in learn if x["section"] == "stotram") + 1
        learn.append(item)

    # Opening — Śuklāmbaradharam through yasya smaraṇa (+ oṃ namo viṣṇave)
    opening_verses = [purva[i] for i in OPENING_IDX]
    opening_verses[-1] = merge_verses(purva, (7, 8))
    for v, en, cue in zip(opening_verses, OPENING_EN, cues["opening"]):
        add("opening", v, en, cue)

    # Pūrva pīṭhikā dialogue + nyāsa — all sung in her recording
    purva_cues = cues["purva"]
    for (idxs, en), cue in zip(PURVA_ITEMS, purva_cues[:-1]):
        add("purva", merge_verses(purva, idxs), en, cue)
    add("purva", NYASA, NYASA["en"], purva_cues[-1])

    # Dhyānam — all eight, as sung
    for i, (v, cue) in enumerate(zip(dhyana, cues["dhyana"])):
        add("dhyana", v, DHYANA_EN.get(i, "A meditation verse on the form of Vishnu."), cue)

    # The 108 name-ślokas
    for i, (v, cue) in enumerate(zip(numbered, cues["stotram"][:107])):
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
        sa = re.sub(r"^हरिः ॐ । ॐ ", "ॐ ", v["sa"])
        iast = re.sub(r"^hariḥ oṃ \| oṃ ", "oṃ ", v["iast"])
        if i == 106:  # she sings śloka 107's oṃ nama iti tail before the pause
            sa += " सर्वप्रहरणायुध ॐ नम इति ।"
            iast += " sarvapraharaṇāyudha oṃ nama iti |"
        add("stotram", {"sa": sa, "iast": iast}, ESSENCES[i], cue, names)

    vanamali_full = {
        "sa": vanamali["sa"] + " श्रीवासुदेवोऽभिरक्षतु ॐ नम इति ।",
        "iast": vanamali["iast"] + " śrīvāsudevo'bhirakṣatu oṃ nama iti |",
    }
    add(
        "stotram",
        vanamali_full,
        ESSENCES[107] + " She sings this closing śloka three times.",
        cues["stotram"][107],
    )

    # Phalaśruti — every verse she sings, in her order
    for (idxs, en), cue in zip(PHALA_ITEMS, cues["phalashruti"]):
        add("phalashruti", merge_verses(phala, idxs), en, cue)

    listen = [
        {
            "section": v["section"],
            "sa": v["sa"],
            "iast": v["iast"],
            "en": v["en"],
            "start": v["start"],
            "end": v["end"],
            "learnId": v["id"],
        }
        for v in learn
    ]

    payload = {
        "meta": {
            "titleSa": "श्रीविष्णुसहस्रनामस्तोत्रम्",
            "titleEn": "Śrī Viṣṇu Sahasranāmam",
            "subtitle": "A quiet companion for learning the thousand names, one verse at a time.",
            "source": "Mahabharata, Anushasana Parva. Recension commonly recited with Shankara’s tradition.",
            "audioNote": "M. S. Subbulakshmi’s recitation is still under copyright, so it is not bundled here. Load your own copy of her recording (many households already have it). The listen view will scroll with the audio.",
            "reciter": "M. S. Subbulakshmi",
            "timing": {
                "id": "mss-1781",
                "label": "M. S. Subbulakshmi — full recitation (29:41)",
                "duration": timing["duration"],
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
