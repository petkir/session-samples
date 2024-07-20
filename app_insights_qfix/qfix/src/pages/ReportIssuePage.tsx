// src/pages/ReportIssuePage.tsx
import React, { useState } from 'react';
import { issueReportingService } from '../services/IssueReportingService';
import { useQFix } from '../contexts/QFixProvider';

const ReportIssuePage: React.FC = () => {
  const { incrementIssueCount} = useQFix();
  const [description, setDescription] = useState('');
  const [photo, setPhoto] = useState<File | null>(null);

  const handleSave = async () => {
    if (photo && description) {
      await issueReportingService.submitIssue(description, photo);
      incrementIssueCount();
    }
  };

  return (
    <div>
      <input type="file" accept="image/*" capture onChange={(e) => setPhoto(e.target.files?.[0] || null)} />
      <textarea placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
      <button onClick={handleSave}>Save</button>
    </div>
  );
};

export default ReportIssuePage;