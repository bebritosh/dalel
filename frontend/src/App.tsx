import { HashRouter, Route, Routes } from "react-router-dom";
import { I18nProvider } from "./i18n";
import { UploadPage } from "./pages/UploadPage";
import { ReviewPage } from "./pages/ReviewPage";
import { ClaimPage } from "./pages/ClaimPage";

export default function App() {
  return (
    <I18nProvider>
      <HashRouter>
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/case/:id/review" element={<ReviewPage />} />
          <Route path="/case/:id/claim" element={<ClaimPage />} />
        </Routes>
      </HashRouter>
    </I18nProvider>
  );
}
