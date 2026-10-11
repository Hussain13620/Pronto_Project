var translations = {
            kn: {
                pageTitle: "ಕೆಲಸಗಾರರಾಗಿ ಸೇರಿ - KAAMKAAJ",
                title: "ಕೆಲಸಗಾರರಾಗಿ ಸೇರಿ",
                intro: "KAAMKAAJ ಗೆ ಸೇರಲು ನಿಮ್ಮ ವಿವರಗಳನ್ನು ಭರ್ತಿ ಮಾಡಿ.",
                name: "ಪೂರ್ಣ ಹೆಸರು",
                phone: "ದೂರವಾಣಿ ಸಂಖ್ಯೆ",
                dob: "ಹುಟ್ಟಿದ ದಿನಾಂಕ",
                address: "ವಿಳಾಸ",
                aadhaar: "ಆಧಾರ್ ಸಂಖ್ಯೆ",
                idProof: "ಗುರುತಿನ ಚೀಟಿ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
                photo: "ನಿಮ್ಮ ಫೋಟೋ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
                services: "ನೀವು ನೀಡುವ ಸೇವೆಗಳು",
                svcCleaning: "ಸ್ವಚ್ಛತೆ",
                svcMopping: "ನೆಲ ಒರೆಸುವುದು",
                svcWashing: "ಪಾತ್ರೆ ತೊಳೆಯುವುದು",
                svcLaundry: "ಬಟ್ಟೆ ಒಗೆಯುವುದು",
                svcDusting: "ಧೂಳು ತೆಗೆಯುವುದು",
                experience: "ಅನುಭವ",
                experiencePlaceholder: "ಉದಾಹರಣೆ: 2 ವರ್ಷಗಳು",
                submit: "ಕೆಲಸಗಾರರಾಗಿ ಸೇರಿ",
                langLabel: "ಭಾಷೆ:"
            },
            en: {
                pageTitle: "Join as a Worker - KAAMKAAJ",
                title: "Join as a Worker",
                intro: "Fill in your details to join KAAMKAAJ.",
                name: "Full Name",
                phone: "Phone Number",
                dob: "Date of Birth",
                address: "Address",
                aadhaar: "Aadhaar Number",
                idProof: "Upload ID Proof",
                photo: "Upload Your Photo",
                services: "Services You Provide",
                svcCleaning: "Cleaning",
                svcMopping: "Mopping",
                svcWashing: "Washing Vessels",
                svcLaundry: "Laundry",
                svcDusting: "Dusting",
                experience: "Experience",
                experiencePlaceholder: "Example: 2 years",
                submit: "Join as a Worker",
                langLabel: "Language:"
            },
            hi: {
                pageTitle: "कामगार के रूप में जुड़ें - KAAMKAAJ",
                title: "कामगार के रूप में जुड़ें",
                intro: "KAAMKAAJ से जुड़ने के लिए अपनी जानकारी भरें।",
                name: "पूरा नाम",
                phone: "फोन नंबर",
                dob: "जन्म तिथि",
                address: "पता",
                aadhaar: "आधार नंबर",
                idProof: "पहचान पत्र अपलोड करें",
                photo: "अपनी फोटो अपलोड करें",
                services: "आप कौन-सी सेवाएं देते हैं",
                svcCleaning: "सफाई",
                svcMopping: "पोछा लगाना",
                svcWashing: "बर्तन धोना",
                svcLaundry: "कपड़े धोना",
                svcDusting: "धूल साफ करना",
                experience: "अनुभव",
                experiencePlaceholder: "उदाहरण: 2 साल",
                submit: "कामगार के रूप में जुड़ें",
                langLabel: "भाषा:"
            }
        };

        function applyLanguage(lang) {
            var dict = translations[lang] || translations.kn;

            document.title = dict.pageTitle;

            var langLabelEl = document.querySelector(".language label");
            if (langLabelEl) {
                langLabelEl.textContent = dict.langLabel;
            }

            var elements = document.querySelectorAll("[data-i18n]");
            for (var i = 0; i < elements.length; i++) {
                var key = elements[i].getAttribute("data-i18n");
                if (dict[key] !== undefined) {
                    elements[i].textContent = dict[key];
                }
            }

            var placeholderElements = document.querySelectorAll("[data-i18n-placeholder]");
            for (var j = 0; j < placeholderElements.length; j++) {
                var pKey = placeholderElements[j].getAttribute("data-i18n-placeholder");
                if (dict[pKey] !== undefined) {
                    placeholderElements[j].setAttribute("placeholder", dict[pKey]);
                }
            }

            document.documentElement.setAttribute("lang", lang);
        }

        document.addEventListener("DOMContentLoaded", function () {
            var select = document.getElementById("languageSelect");
            if (select) {
                select.addEventListener("change", function () {
                    applyLanguage(this.value);
                });
            }
        });