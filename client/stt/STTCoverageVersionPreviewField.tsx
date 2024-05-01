import * as React from 'react';

import {ICoverageMetadataPreviewProps} from 'newsroom-core/assets/interfaces';
import {exposed} from 'newsroom-core';

export function STTCoverageVersionPreviewField({coverage, fullCoverage}: ICoverageMetadataPreviewProps) {
    const {gettext} = exposed.locale;

    if (fullCoverage == null) {
        console.warn(`Unable to find the full coverage for ${coverage.coverage_id}`);
        return null;
    }

    const sttVersion = (fullCoverage.planning?.subjects || []).filter(
        (subject) => subject.scheme === 'sttversion'
    );

    return sttVersion.length === 0 ? null : (
        <div className="coverage-item__row align-items-center">
            <span className="coverage-item__text-label me-1">{gettext('Version')}:</span>
            <span>{sttVersion[0].name}</span>
        </div>
    );
}
