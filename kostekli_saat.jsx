// Köstekli Cep Saati - Sallanan Animasyon
// After Effects'te: File > Scripts > Run Script File...  ile bu dosyayı seçin.
// Script yeni bir kompozisyon kurar: zincire asılı bir cep saati sarkaç gibi sallanır,
// akrep / yelkovan / saniye ibresi de çalışır.
//
// Ayar: "Salınım Merkezi" null katmanındaki iki slider ile
//   - Salınım Açısı (derece)
//   - Salınım Süresi (bir tam gidiş-dönüş, saniye)
// değiştirilebilir.

(function kostekliSaat() {
    // ---------------- Ayarlar ----------------
    var W = 1920, H = 1080, FPS = 30, SURE = 10;
    var PIVOT = [W / 2, 70];          // zincirin asıldığı nokta
    var LINK = 20, LINK_SAYISI = 16;  // zincir halkaları
    var ZINCIR = LINK * LINK_SAYISI;  // zincir uzunluğu (px)
    var R = 170;                      // kasa yarıçapı
    var RD = 148;                     // kadran yarıçapı
    var C = R + 110;                  // halka tepesinden saat merkezine mesafe
    var ACI = 22;                     // salınım açısı (derece)
    var PERIYOT = 2.5;                // bir tam salınım (saniye) -> 10 sn'de 4 tur, kusursuz döngü

    function hex(h) {
        return [parseInt(h.substr(1, 2), 16) / 255,
                parseInt(h.substr(3, 2), 16) / 255,
                parseInt(h.substr(5, 2), 16) / 255];
    }
    function hex4(h) { var c = hex(h); c.push(1); return c; }

    var ALTIN_KOYU = hex("#7a5a17");
    var ALTIN = hex("#c9a13b");
    var ALTIN_ACIK = hex("#e9cf7a");
    var ALTIN_PARLAK = hex("#f8eab0");
    var KONTUR = hex("#3f2d0a");
    var KADRAN = hex("#f4ecd8");
    var KADRAN_KENAR = hex("#b89b5e");
    var MUREKKEP = hex("#2a2420");
    var IBRE = hex("#1d2436");
    var KIRMIZI = hex("#b22a1f");

    var comp;

    // ---------------- Yardımcılar ----------------
    function tr(layer, ad) { return layer.property("ADBE Transform Group").property(ad); }
    function efekt(layer, ad) { return layer.property("ADBE Effect Parade").addProperty(ad); }

    function katman(ad, ebeveyn, poz) {
        var l = comp.layers.addShape();
        l.name = ad;
        if (ebeveyn) l.parent = ebeveyn;
        tr(l, "ADBE Anchor Point").setValue([0, 0]);
        tr(l, "ADBE Position").setValue(poz);
        l.motionBlur = true;
        return l;
    }

    // Not: Shape katmanlarında listede üstte olan grup önde çizilir.
    // addProperty sona eklediği için gruplar ÖNDEN ARKAYA doğru eklenir.
    function grup(layer, ad) {
        var g = layer.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group");
        g.name = ad;
        return g;
    }
    function icerik(g) { return g.property("ADBE Vectors Group"); }

    function elips(g, boyut, poz) {
        var e = icerik(g).addProperty("ADBE Vector Shape - Ellipse");
        e.property("ADBE Vector Ellipse Size").setValue(boyut);
        e.property("ADBE Vector Ellipse Position").setValue(poz);
    }
    function dikdortgen(g, boyut, poz, yuvarlak) {
        var r = icerik(g).addProperty("ADBE Vector Shape - Rect");
        r.property("ADBE Vector Rect Size").setValue(boyut);
        r.property("ADBE Vector Rect Position").setValue(poz);
        if (yuvarlak) r.property("ADBE Vector Rect Roundness").setValue(yuvarlak);
    }
    function yol(g, noktalar, kapali) {
        var p = icerik(g).addProperty("ADBE Vector Shape - Group");
        var s = new Shape();
        s.vertices = noktalar;
        s.closed = kapali;
        p.property("ADBE Vector Shape").setValue(s);
    }
    function dolgu(g, renk, opaklik) {
        var f = icerik(g).addProperty("ADBE Vector Graphic - Fill");
        f.property("ADBE Vector Fill Color").setValue(renk);
        if (opaklik !== undefined) f.property("ADBE Vector Fill Opacity").setValue(opaklik);
    }
    function cizgi(g, renk, kalinlik, uc) {
        var s = icerik(g).addProperty("ADBE Vector Graphic - Stroke");
        s.property("ADBE Vector Stroke Color").setValue(renk);
        s.property("ADBE Vector Stroke Width").setValue(kalinlik);
        if (uc) s.property("ADBE Vector Stroke Line Cap").setValue(uc); // 1 düz, 2 yuvarlak
    }
    function radyal(r, derece) {
        var a = derece * Math.PI / 180;
        return [r * Math.sin(a), -r * Math.cos(a)];
    }
    function bulanik(layer, miktar) {
        try { efekt(layer, "ADBE Gaussian Blur 2").property(1).setValue(miktar); } catch (e) {}
    }

    // ---------------- Kurulum ----------------
    function kur() {
        var proj = app.project || app.newProject();
        comp = proj.items.addComp("Köstekli Saat", W, H, 1, SURE, FPS);
        comp.bgColor = hex("#121010");
        comp.motionBlur = true;

        // Arka plan (radyal degrade)
        var bg = comp.layers.addSolid(hex("#1a1614"), "Arka Plan", W, H, 1, SURE);
        try {
            var ramp = efekt(bg, "ADBE Ramp");
            ramp.property(1).setValue([W / 2, H * 0.45]);
            ramp.property(2).setValue(hex4("#4a3d33"));
            ramp.property(3).setValue([W / 2 + 1100, H * 0.45]);
            ramp.property(4).setValue(hex4("#0c0a09"));
            ramp.property(5).setValue(2); // radyal
        } catch (e) {}

        // Salınım merkezi: tüm düzenek bunun etrafında döner
        var pivot = comp.layers.addNull(SURE);
        pivot.name = "Salınım Merkezi";
        tr(pivot, "ADBE Anchor Point").setValue([0, 0]);
        tr(pivot, "ADBE Position").setValue(PIVOT);

        // Zincirin ucu: saat buna bağlı, hafif gecikmeli ikincil hareket yapar
        var saatBag = comp.layers.addNull(SURE);
        saatBag.name = "Saat Bağlantısı";
        tr(saatBag, "ADBE Anchor Point").setValue([0, 0]);
        saatBag.parent = pivot;
        tr(saatBag, "ADBE Position").setValue([0, ZINCIR]);

        // Duvardaki gölge
        var golge = katman("Gölge", saatBag, [14, C + 24]);
        var g = grup(golge, "Gölge");
        elips(g, [2 * R + 6, 2 * R + 6], [0, 0]);
        dolgu(g, [0, 0, 0]);
        tr(golge, "ADBE Opacity").setValue(55);
        bulanik(golge, 28);

        // Köstek zinciri
        var zincir = katman("Köstek Zinciri", pivot, [0, 0]);
        var i;
        g = grup(zincir, "Halkalar (yandan)");
        for (i = 1; i < LINK_SAYISI; i += 2) dikdortgen(g, [6, 28], [0, LINK / 2 + i * LINK], 3);
        cizgi(g, KONTUR, 1.5);
        dolgu(g, ALTIN_ACIK);
        g = grup(zincir, "Halkalar (önden)");
        for (i = 0; i < LINK_SAYISI; i += 2) elips(g, [16, 28], [0, LINK / 2 + i * LINK]);
        cizgi(g, ALTIN, 4);
        cizgi(g, KONTUR, 6.5);

        // Askı çivisi
        var civi = katman("Askı Çivisi", null, PIVOT);
        g = grup(civi, "Parlama");
        elips(g, [7, 7], [-4, -4]);
        dolgu(g, hex("#9a9a9a"));
        g = grup(civi, "Çivi");
        elips(g, [22, 22], [0, 0]);
        cizgi(g, hex("#555555"), 2);
        dolgu(g, hex("#2b2b2b"));

        // Saat kasası (halka, kurma topuzu, kasa)
        var kasa = katman("Saat Kasası", saatBag, [0, C]);
        g = grup(kasa, "İç Halka");
        elips(g, [2 * (RD + 4), 2 * (RD + 4)], [0, 0]);
        dolgu(g, ALTIN_KOYU);
        g = grup(kasa, "Çerçeve");
        elips(g, [2 * (R - 12), 2 * (R - 12)], [0, 0]);
        dolgu(g, ALTIN_ACIK);
        g = grup(kasa, "Parlama");
        elips(g, [2 * (R - 12), 2 * (R - 12)], [-5, -5]);
        dolgu(g, ALTIN_PARLAK, 70);
        g = grup(kasa, "Gölgelik");
        elips(g, [2 * (R - 12), 2 * (R - 12)], [5, 5]);
        dolgu(g, ALTIN_KOYU, 45);
        g = grup(kasa, "Kasa");
        elips(g, [2 * (R - 4), 2 * (R - 4)], [0, 0]);
        dolgu(g, ALTIN);
        g = grup(kasa, "Dış Kenar");
        elips(g, [2 * R, 2 * R], [0, 0]);
        dolgu(g, KONTUR);
        g = grup(kasa, "Kurma Dişleri");
        for (i = -18; i <= 18; i += 6) yol(g, [[i, -195], [i, -170]], false);
        cizgi(g, ALTIN_KOYU, 2);
        g = grup(kasa, "Kurma Topuzu");
        dikdortgen(g, [50, 30], [0, -182], 8);
        cizgi(g, KONTUR, 1.5);
        dolgu(g, ALTIN);
        g = grup(kasa, "Sap");
        dikdortgen(g, [12, 28], [0, -208], 2);
        cizgi(g, KONTUR, 1);
        dolgu(g, ALTIN_KOYU);
        g = grup(kasa, "Halka");
        elips(g, [64, 58], [0, -C + 29]);
        cizgi(g, ALTIN, 8);
        cizgi(g, KONTUR, 11);

        // Kadran
        var kadran = katman("Kadran", saatBag, [0, C]);
        g = grup(kadran, "Saat Çizgileri");
        for (i = 0; i < 12; i++) yol(g, [radyal(122, i * 30), radyal(140, i * 30)], false);
        cizgi(g, MUREKKEP, 4.5, 1);
        g = grup(kadran, "Dakika Çizgileri");
        for (i = 0; i < 60; i++) {
            if (i % 5 === 0) continue;
            yol(g, [radyal(129, i * 6), radyal(140, i * 6)], false);
        }
        cizgi(g, MUREKKEP, 1.8, 1);
        g = grup(kadran, "Dakika Yolu");
        elips(g, [280, 280], [0, 0]);
        elips(g, [258, 258], [0, 0]);
        cizgi(g, MUREKKEP, 1.2);
        g = grup(kadran, "Kadran Zemini");
        elips(g, [2 * RD, 2 * RD], [0, 0]);
        cizgi(g, KADRAN_KENAR, 2);
        dolgu(g, KADRAN);

        // Romen rakamları
        var rakamlar = ["XII", "I", "II", "III", "IIII", "V", "VI", "VII", "VIII", "IX", "X", "XI"];
        var BOYUT = 28;
        for (i = 0; i < 12; i++) {
            var p = radyal(95, i * 30);
            var t = comp.layers.addText(rakamlar[i]);
            t.name = "Rakam " + rakamlar[i];
            var tp = t.property("ADBE Text Properties").property("ADBE Text Document");
            var td = tp.value;
            try { td.resetCharStyle(); td.resetParagraphStyle(); } catch (e) {}
            try { td.font = "Georgia"; } catch (e) {}
            td.fontSize = BOYUT;
            td.applyFill = true;
            td.fillColor = MUREKKEP;
            td.applyStroke = false;
            td.justification = ParagraphJustification.CENTER_JUSTIFY;
            tp.setValue(td);
            t.parent = saatBag;
            tr(t, "ADBE Position").setValue([p[0], C + p[1] + BOYUT * 0.36]);
            t.motionBlur = true;
        }

        // Akrep
        var akrep = katman("Akrep", saatBag, [0, C]);
        g = grup(akrep, "Halka");
        elips(g, [20, 20], [0, -58]);
        cizgi(g, IBRE, 3.5);
        g = grup(akrep, "İbre");
        yol(g, [[-5.5, 16], [5.5, 16], [3.2, -44], [0, -86], [-3.2, -44]], true);
        elips(g, [18, 18], [0, 0]);
        dolgu(g, IBRE);

        // Yelkovan
        var yelkovan = katman("Yelkovan", saatBag, [0, C]);
        g = grup(yelkovan, "İbre");
        yol(g, [[-4, 18], [4, 18], [2.2, -100], [0, -130], [-2.2, -100]], true);
        elips(g, [14, 14], [0, 0]);
        dolgu(g, IBRE);

        // Saniye ibresi
        var saniye = katman("Saniye", saatBag, [0, C]);
        g = grup(saniye, "Merkez");
        elips(g, [11, 11], [0, 26]);
        elips(g, [9, 9], [0, 0]);
        dolgu(g, KIRMIZI);
        g = grup(saniye, "İbre");
        yol(g, [[0, 32], [0, -132]], false);
        cizgi(g, KIRMIZI, 1.8, 2);

        // Merkez pimi
        var pim = katman("Merkez Pimi", saatBag, [0, C]);
        g = grup(pim, "Pim");
        elips(g, [6, 6], [0, 0]);
        cizgi(g, KONTUR, 1);
        dolgu(g, ALTIN);

        // Cam parlaması
        var cam = katman("Cam Parlaması", saatBag, [0, C]);
        g = grup(cam, "Parlama");
        elips(g, [120, 50], [0, 0]);
        dolgu(g, [1, 1, 1], 22);
        g.property("ADBE Vector Transform Group").property("ADBE Vector Position").setValue([-62, -78]);
        g.property("ADBE Vector Transform Group").property("ADBE Vector Rotation").setValue(-38);
        bulanik(cam, 12);

        // ---------------- Hareket (expression'lar) ----------------
        // Tüm parent işlemleri bittikten sonra eklenir.
        var s1 = efekt(pivot, "ADBE Slider Control");
        s1.name = "Salınım Açısı";
        s1.property(1).setValue(ACI);
        var s2 = efekt(pivot, "ADBE Slider Control");
        s2.name = "Salınım Süresi (sn)";
        s2.property(1).setValue(PERIYOT);

        tr(pivot, "ADBE Rotate Z").expression =
            "var aci = effect(1)(1);\n" +
            "var periyot = Math.max(0.1, effect(2)(1));\n" +
            "aci * Math.sin(2 * Math.PI * time / periyot);";

        // Saat, zincirin ucunda ataletle hafifçe geride kalır
        tr(saatBag, "ADBE Rotate Z").expression =
            "var r = parent.transform.rotation;\n" +
            "0.3 * (r.valueAtTime(time - 0.15) - r.value);";

        // Saat 10:10:35'ten başlayarak gerçek hızda işler
        var BASLA = "var s = 36635 + time;\n";
        tr(akrep, "ADBE Rotate Z").expression = BASLA + "(s / 3600 % 12) * 30;";
        tr(yelkovan, "ADBE Rotate Z").expression = BASLA + "(s / 60 % 60) * 6;";
        tr(saniye, "ADBE Rotate Z").expression = BASLA + "(Math.floor(s * 5) / 5 % 60) * 6;";

        // Null'lar en üste
        saatBag.moveToBeginning();
        pivot.moveToBeginning();

        comp.time = 0;
        comp.openInViewer();
        alert("Köstekli saat hazır!\nOynatmak için Boşluk (Space) tuşuna basın.");
    }

    app.beginUndoGroup("Köstekli Saat");
    try {
        kur();
    } catch (err) {
        alert("Hata: " + err.toString() + (err.line ? " (satır " + err.line + ")" : ""));
    }
    app.endUndoGroup();
})();
